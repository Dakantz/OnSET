import numpy as np

# %%
import sys
import os

from model import SubjectLink

sys.path.insert(0, os.path.abspath("../.."))
sys.path.append(os.path.abspath("../../backend"))
sys.path.append(os.path.abspath(""))

import networkx as nx

from langchain_core.prompts import ChatPromptTemplate
from typing import TypeVar
from sqlalchemy.orm import aliased, Session
from sqlalchemy.sql import text
from rdflib.plugins.stores.sparqlstore import SPARQLStore
from model import Subject
from pydantic import BaseModel, Field, create_model

from ontology import OntologyManager, OntologyConfig, Graph
from explorative.explorative_support import GuidanceManager, select
from explorative.exp_model import (
    SubjectInDB,
    SubjectLinkDB,
)
from tqdm import tqdm
import pandas as pd
import re
SL = TypeVar("SL")

top_k = 100
seed = 42


class Constraint(BaseModel):
    property: str
    value: str | None
    modifier: str | None


class Entity(BaseModel):
    identifier: str
    type: str
    constraints: list[Constraint] = Field([])


class Relation(BaseModel):
    entity: str
    relation: str
    target: str


class EntitiesRelations(BaseModel):
    relations: list[Relation] = Field([])
    entities: list[Entity] = Field([])
    message: str = Field("Found Relations and Entities")


class CandidateRelation(Relation):
    score: float
    link: SubjectLink | None = Field(None)


class CandidateConstraint(Constraint):
    score: float
    type: str
    property: str
    entity: str
    link: SubjectLink | None = Field(None)


class CandidateEntity(Entity):
    score: float
    type: str
    subject: Subject | None = Field(None)


class Candidates(EntitiesRelations):
    relations: list[CandidateRelation] = Field([])
    entities: list[CandidateEntity] = Field([])
    # constraints: list[CandidateConstraint] = Field([])


class EnrichedConstraint(Constraint):
    constraint: SubjectLink | None


class EnrichedEntity(Entity):
    subject: Subject
    # constraints: list[EnrichedConstraint] = Field([])


class EnrichedRelation(Relation):
    link: SubjectLink | None


class EnrichedEntitiesRelations(EntitiesRelations):
    relations: list[EnrichedRelation] = Field([])
    entities: list[EnrichedEntity] = Field([])


class QueryProgress(BaseModel):
    id: str
    start_time: str
    progress: int = Field(0)
    max_steps: int
    message: str = Field("")
    relations_steps: list[
        EntitiesRelations | Candidates | EnrichedEntitiesRelations
    ] = Field([])
    enriched_relations: EnrichedEntitiesRelations | None = None


class EnrichedDBEntity(Entity, arbitrary_types_allowed=True):
    subject: SubjectInDB | Subject | None


class EnrichedDBRelation(Relation, arbitrary_types_allowed=True):
    link: SubjectLinkDB | SubjectLink | None


def safe_prob(probs: np.array):
    if np.sum(probs) == 0:
        return np.ones(len(probs)) / len(probs)
    else:
        return probs / probs.sum()


def choose_entity(
    links: list[tuple[str, SL]], rs: np.random.RandomState
) -> tuple[str, SL]:
    probs = np.array([link[1].instance_count for link in links])
    probs = safe_prob(probs)
    indices = np.arange(len(links))
    choice: int = rs.choice(indices, p=probs)
    return links[choice]


def random_downgrade(cls: SubjectInDB, rs: np.random.RandomState) -> SubjectInDB:
    def get_subclasses(subcls: SubjectInDB):
        subclasses = [subcls.sub_classes] + [
            get_subclasses(sub) for sub in subcls.sub_classes
        ]
        return [sub for sublist in subclasses for sub in sublist]

    # print(f"downgrading {cls.label}", [sc.label for sc in cls.sub_classes])
    subclasses = [cls] + get_subclasses(cls)
    probs = np.array([float(sc.instance_count) for sc in subclasses])
    probs = safe_prob(probs)
    # print(f"{cls.label} probs", probs)
    choice = rs.choice(np.arange(len(subclasses)), p=probs)
    return subclasses[choice]


def choose_graph(
    max_nodes=4, top_k=top_k, seed=seed, max_tries=5, guidance_man: GuidanceManager = None
):
    rs = np.random.RandomState(seed)
    with Session(guidance_man.engine) as session:
        session.execute(text("SET TRANSACTION READ ONLY"))
        session.autoflush = False

        def downgrade_link_subjects(link: SubjectLinkDB):
            from_downgrade = random_downgrade(link.from_subject, rs)
            to_downgrade = random_downgrade(link.to_subject, rs)
            link.from_id = from_downgrade.subject_id
            link.to_id = to_downgrade.subject_id
            link.from_subject = from_downgrade
            link.to_subject = to_downgrade
            return link

        from_subject_alias = aliased(SubjectInDB, name="from_subject")
        to_subject_alias = aliased(SubjectInDB, name="to_subject")
        # from and start links do not start with underscore _
        best_links_db = session.execute(
            select(SubjectLinkDB)
            .where(SubjectLinkDB.from_id != SubjectLinkDB.to_id)
            .where(SubjectLinkDB.to_id != None)
            .where(SubjectLinkDB.from_id.not_like("!_:%", "!"))
            .where(SubjectLinkDB.to_id.not_like("!_:%", "!"))
            .where(SubjectLinkDB.description.not_like("%<%"))
            .where(SubjectLinkDB.description.not_like("%>%"))
            .order_by(SubjectLinkDB.instance_count.desc())
            .join(
                from_subject_alias,
                SubjectLinkDB.from_subject.of_type(from_subject_alias),
            )
            .join(to_subject_alias, SubjectLinkDB.to_subject.of_type(to_subject_alias))
            # .options(
            #     lazyload(SubjectLinkDB.from_subject.of_type(from_subject_alias)),
            #     lazyload(SubjectLinkDB.to_subject.of_type(to_subject_alias)),
            # )
            .limit(top_k)
        ).all()
        best_links: list[tuple[str, SubjectLinkDB]] = [
            (link[0].property_id, link[0]) for link in best_links_db
        ]
        _, choice = choose_entity(best_links, rs)
        choice_downgraded = downgrade_link_subjects(choice)
        id_counter = 0

        def id_counter_gen():
            nonlocal id_counter
            id_counter += 1
            return id_counter

        current_links = [
            EnrichedDBRelation(
                entity=f"{choice_downgraded.from_subject.label} {id_counter_gen()}",
                relation=choice_downgraded.label,
                target=f"{choice_downgraded.to_subject.label} {id_counter_gen()}",
                link=choice_downgraded,
            )
        ]

        def nodes_from_links(links: list[EnrichedDBRelation]):
            all_subjects = [
                [
                    (link.entity, link.link.from_subject, link),
                    (link.target, link.link.to_subject, link),
                ]
                for link in links
            ]
            all_subjects = [subj for sublist in all_subjects for subj in sublist]
            return {
                id: EnrichedDBEntity(
                    identifier=id,
                    type=subject.label,
                    subject=subject,
                )
                for id, subject, link in all_subjects
            }

        current_nodes = nodes_from_links(current_links)
        retries = 0
        while len(current_nodes) < max_nodes:
            start_id, start_node = choose_entity(
                list([(nd.identifier, nd.subject) for nd in current_nodes.values()]), rs
            )
            left_right = rs.choice([0, 1])
            extending_to = left_right == 0
            query = (
                select(SubjectLinkDB)
                .where(SubjectLinkDB.from_id != SubjectLinkDB.to_id)
                .where(SubjectLinkDB.to_id is not None)
                .where(SubjectLinkDB.from_id.not_like("!_:%", "!"))
                .where(SubjectLinkDB.to_id.not_like("!_:%", "!"))
                .where(SubjectLinkDB.description.not_like("%<%"))
                .where(SubjectLinkDB.description.not_like("%>%"))
                .join(
                    from_subject_alias,
                    SubjectLinkDB.from_subject.of_type(from_subject_alias),
                )
                .join(
                    to_subject_alias, SubjectLinkDB.to_subject.of_type(to_subject_alias)
                )
                .filter(
                    SubjectLinkDB.link_id.not_in(
                        [link.link.link_id for link in current_links]
                    )
                )
            )
            if extending_to:
                query = query.where(SubjectLinkDB.from_id == start_node.subject_id)
            else:
                query = query.where(SubjectLinkDB.to_id == start_node.subject_id)
            # print("Extending to", start_node.label, "extending_to", extending_to)
            new_links = session.execute(
                query.order_by(SubjectLinkDB.instance_count.desc()).limit(top_k)
            ).all()
            new_links: list[tuple[str, SubjectLinkDB]] = [
                (link[0].property_id, link[0]) for link in new_links
            ]
            if len(new_links) == 0:
                if retries >= max_tries:
                    break
                retries += 1
                continue
            chosen_link_id, chosen_link = choose_entity(new_links, rs)

            extending_direction = (
                (chosen_link.from_subject, chosen_link.to_subject)
                if extending_to
                else (chosen_link.to_subject, chosen_link.from_subject)
            )

            downgraded_extend = random_downgrade(extending_direction[1], rs)
            # print(
            #     "Downgraded from",
            #     extending_direction[1].label,
            #     downgraded_extend.label,
            #     "on link",
            #     choice.label,
            # )
            if extending_to:
                entity, target = (
                    start_id,
                    f"{downgraded_extend.label} {id_counter_gen()}",
                )
                chosen_link.to_id = downgraded_extend.subject_id
                chosen_link.to_subject = downgraded_extend
            else:
                entity, target = (
                    f"{downgraded_extend.label} {id_counter_gen()}",
                    start_id,
                )
                chosen_link.from_id = downgraded_extend.subject_id
                chosen_link.from_subject = downgraded_extend
            current_links.append(
                EnrichedDBRelation(
                    entity=entity,
                    relation=chosen_link.label,
                    target=target,
                    link=chosen_link,
                )
            )
            current_nodes = nodes_from_links(current_links)
        enriched_erl = EnrichedEntitiesRelations(
            entities=[
                EnrichedEntity(
                    subject=guidance_man.oman.enrich_subject(entity.subject.subject_id),
                    **entity.model_dump(exclude=["subject"]),
                )
                for entity in current_nodes.values()
            ],
            relations=[
                EnrichedRelation(
                    link=relation.link.from_db(guidance_man.oman),
                    **relation.model_dump(exclude=["link"]),
                )
                for relation in current_links
            ],
        )
        # remove numbers from identifiers if they are unique!
        simplifyable_entities:dict[str,EnrichedEntity] = {}
        unique_types = set([entity.type for entity in enriched_erl.entities])
        for unique_type in unique_types:
            using_type = [
                entity for entity in enriched_erl.entities if entity.type == unique_type
            ]
            if len(using_type) == 1:
                simplifyable_entities[using_type[0].identifier] = using_type[0]
        for entity in simplifyable_entities.values():
            entity.identifier = re.sub(r" \d+$", "", entity.identifier)
        for link in enriched_erl.relations:
            if link.entity in simplifyable_entities.keys():
                link.entity = re.sub(r" \d+$", "", link.entity)
            if link.target in simplifyable_entities.keys():
                link.target = re.sub(r" \d+$", "", link.target)

        return enriched_erl


def erl_to_templated_query(erl: EnrichedEntitiesRelations):
    qs = []
    for rel in erl.relations:
        qs.append(f"a {rel.entity} has a {rel.relation} with {rel.target}")
    return ", and ".join(qs)


def reduce_erl(erl: EnrichedEntitiesRelations):
    reduced_erl = EntitiesRelations(entities=erl.entities, relations=erl.relations)
    return reduced_erl
