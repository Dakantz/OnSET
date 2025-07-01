from llama_cpp.llama import Llama, LlamaGrammar

from sqlalchemy import select, text, func, and_
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field, create_model
from enum import Enum
import datetime
from fastapi import BackgroundTasks
import numpy as np
import tqdm

from utils import escape_sparql_var, fix_json

from explorative.explorative_support import GuidanceManager
from explorative.exp_model import (
    FuzzyQuery,
    RETURN_TYPE,
    RELATION_TYPE,
    SubjectLinkDB,
    SubjectInDB,
    SampledGraphDB,
    GraphLinkDB,
    GraphEntityDB,
    BasePostgres,
)
from explorative.exp_model import Subject, SubjectLink

# has to be installed from fork until merged!
from llama_cpp_agent.gbnf_grammar_generator.gbnf_grammar_from_pydantic_models import (
    generate_gbnf_grammar_from_pydantic_models,
)
from redis_cache import RedisCache
from explorative.llm_query_gen import (
    choose_graph,
    erl_to_templated_query,
    reduce_erl,
    Entity,
    EntitiesRelations,
    Constraint,
    Relation,
    EnrichedEntitiesRelations,
    EnrichedEntity,
    EnrichedRelation,
    EnrichedConstraint,
    Candidates,
    CandidateEntity,
    CandidateRelation,
    CandidateConstraint,
    QueryProgress,
)
from initiator import Initationatable

# System prompt describes information given to all conversations
ERL_PROMPT_SYSTEM = """
Return all the entity relations and constraint within the prompt in the form of JSON output. The output should be a list of all entities and their constraints, as well as the relations between them. Make sure to include all entities and targets in the list of entities. Constraints should only be included in the list of entities they are associated with.
"""
ERL_SAMPLE = EntitiesRelations(
    relations=[
        Relation(entity="person 1", relation="author", target="work 1"),
        Relation(entity="person 1", relation="birth place", target="place 1"),
    ],
    entities=[
        Entity(
            identifier="person 1",
            type="person",
            constraints=[
                Constraint(property="birth_date", value="1990", modifier="greater_than")
            ],
        ),
        Entity(identifier="work 1", type="work", constraints=[]),
        Entity(identifier="place 1", type="place", constraints=[]),
    ],
)
# Example prompt demonstrating the output we are looking for
ERL_PROMPT_EXAMPLE = (
    "the birth place of an author of a work where the author is born after 1990",
    ERL_SAMPLE.model_dump_json(),
)

ERL_PROMPT_QUERY_GEN = """You are a helpful assistant turning relational knowledge into natural language."""

RAG_PROMPT_EXAMPLE_CANDIDATES = Candidates(
    relations=[
        CandidateRelation(
            entity="person 1", relation="author", target="work 1", score=0.9
        )
    ],
    entities=[
        CandidateEntity(identifier="person 1", type="person", score=0.9),
        CandidateEntity(identifier="composer 1", type="composer", score=0.7),
        CandidateEntity(identifier="work 1", type="work", score=0.9),
        CandidateEntity(identifier="song 1", type="song", score=0.6),
    ],
    constraints=[
        CandidateConstraint(
            property="birth date",
            value="1990",
            modifier="greater_than",
            score=0.9,
            type="sko:DateTime",
            entity="person 1",
        ),
        CandidateConstraint(
            property="death year",
            value="180cm",
            modifier="greater_than",
            score=0.8,
            type="sko:DateTime",
            entity="person 1",
        ),
    ],
)

RAG_PROMPT_SYSTEM = """
Return all the entity relations and constraint within the prompt in the form of JSON output. The output should be a list of all entities and their constraints, as well as the relations between them. Make sure to include all entities and targets in the list of entities. Constraints should only be included in the list of entities they are associated with.
"""

RAG_PROMPT_EXPECTED_OUTPUT = EntitiesRelations(
    relations=[
        Relation(entity="person 1", relation="author", target="work 1"),
        Relation(entity="person 1", relation="birth place", target="place 1"),
    ],
    entities=[
        Entity(
            identifier="person 1",
            type="person",
            constraints=[
                Constraint(
                    property="birth date",
                    value="1.1.1990",
                    modifier="greater_than",
                )
            ],
        ),
        Entity(identifier="work 1", type="work", constraints=[]),
        Entity(identifier="place 1", type="place", constraints=[]),
    ],
)
RAG_PROMPT_EXAMPLE = (
    ERL_PROMPT_EXAMPLE[0],
    RAG_PROMPT_EXAMPLE_CANDIDATES.model_dump_json(),
    ERL_SAMPLE.model_dump_json(),
)


class LLMQuery(Initationatable):
    def __init__(
        self, topic: GuidanceManager, zero_shot=False, temperature=0.3, max_tokens=2048
    ):
        self.max_tokens = max_tokens
        self.zero_shot = zero_shot
        self.temperature = temperature
        self.guidance_man = topic
        self.gbnf_erl = generate_gbnf_grammar_from_pydantic_models(
            [EntitiesRelations], "EntitiesRelations", add_inner_thoughts=False
        )
        self.grammar_erl = LlamaGrammar.from_string(self.gbnf_erl)

        self.gbnf_candidates = generate_gbnf_grammar_from_pydantic_models(
            [Candidates], "Candidates", add_inner_thoughts=False
        )
        self.grammar_candidates = LlamaGrammar.from_string(self.gbnf_candidates)
        self.query_id_counter = 0
        self.cache = RedisCache[QueryProgress](model=QueryProgress)

    def run_query(
        self, query: str, progress: QueryProgress | None = None, enable_cache=True
    ):
        if progress is None:
            progress = QueryProgress(
                max_steps=5,
                id="query:0",
                start_time=datetime.datetime.now().isoformat(),
                relations_steps=[],
            )
        progress.progress = 1
        progress.message = "Querying entities and relations"
        if enable_cache:
            self.cache[progress.id] = progress

        erl = self.query_erl(query)
        progress.progress = 2
        progress.message = "Fetching possible candidates"
        erl.message = "Found entities and relations"
        progress.relations_steps.append(erl)
        if enable_cache:
            self.cache[progress.id] = progress

        candidates = self.candidates_for_erl(erl)
        progress.progress = 3
        progress.message = "Querying candidates"
        candidates.message = "Found similar candidates"
        progress.relations_steps.append(candidates)
        if enable_cache:
            self.cache[progress.id] = progress

        constrained_erl = self.query_constrained(query, candidates)
        progress.progress = 4
        progress.message = "Enriching results"
        constrained_erl.message = "Constraints applied"
        progress.relations_steps.append(constrained_erl)
        if enable_cache:
            self.cache[progress.id] = progress

        enriched_erl = self.enrich_entities_relations(constrained_erl, candidates)
        progress.progress = 5
        progress.message = "Query completed"
        enriched_erl.message = "Aligned results"
        progress.enriched_relations = enriched_erl
        progress.relations_steps.append(enriched_erl)
        if enable_cache:
            self.cache[progress.id] = progress
        return progress

    def start_query(self, query: str, background_tasks: BackgroundTasks):
        query_id = self.query_id_counter = self.query_id_counter + 1
        start_time = datetime.datetime.now().isoformat()
        query_key = f"query:{query_id}:{start_time}"
        progress = QueryProgress(
            max_steps=5,
            id=query_key,
            start_time=start_time,
            relations_steps=[],
        )
        self.cache[query_key] = progress
        background_tasks.add_task(self.run_query, progress, query)
        return progress

    def query_progress(self, query_id: str) -> QueryProgress:
        return self.cache[query_id]

    @property
    def model(self) -> Llama:
        return self.guidance_man.llama_model

    def query_erl(self, query: str) -> EntitiesRelations:
        messages = [
            {"role": "system", "content": ERL_PROMPT_SYSTEM},
        ]
        if not self.zero_shot:
            messages.extend(
                [
                    {"role": "user", "content": ERL_PROMPT_EXAMPLE[0]},
                    {"role": "assistant", "content": ERL_PROMPT_EXAMPLE[1]},
                ]
            )
        messages.append({"role": "user", "content": query})
        response = self.model.create_chat_completion(
            grammar=self.grammar_erl,
            messages=messages,
            max_tokens=self.max_tokens,
            temperature=self.temperature,
        )
        response_msg = response["choices"][0]["message"]["content"]
        fixed_response = fix_json(response_msg, item_keys=["entities", "relations"])
        return EntitiesRelations.model_validate(fixed_response)

    def query_constrained(
        self, query: str, candidates: Candidates
    ) -> EntitiesRelations:
        ConstrainedEntitiesRelations = self.build_constrained_classes(candidates)
        grammar_constrained = LlamaGrammar.from_string(
            generate_gbnf_grammar_from_pydantic_models(
                [ConstrainedEntitiesRelations],
                "ConstrainedEntitiesRelations",
                add_inner_thoughts=False,
            )
        )
        messages = [
            {"role": "system", "content": RAG_PROMPT_SYSTEM},
        ]
        if not self.zero_shot:
            messages.extend(
                [
                    {"role": "user", "content": RAG_PROMPT_EXAMPLE[0]},
                    {"role": "assistant", "content": RAG_PROMPT_EXAMPLE[2]},
                ]
            )
        messages.append({"role": "user", "content": query})
        response = self.model.create_chat_completion(
            grammar=grammar_constrained,
            messages=messages,
            max_tokens=self.max_tokens,
            temperature=self.temperature,
        )
        response_msg = response["choices"][0]["message"]["content"]
        fixed_response = fix_json(response_msg, item_keys=["entities", "relations"])

        return ConstrainedEntitiesRelations.model_validate(fixed_response)

    def candidates_for_erl(
        self, erl: EntitiesRelations, candidate_limit=3
    ) -> Candidates:
        relation_candidates: list[CandidateRelation] = []
        constraint_candidates: list[CandidateConstraint] = []
        entity_candidates: list[CandidateEntity] = []
        for relation in erl.relations:
            top_results = self.guidance_man.search_fuzzy(
                query=FuzzyQuery(
                    q=f"A {relation.entity} is {relation.relation} of {relation.target}",
                    limit=candidate_limit,
                    type=RETURN_TYPE.LINK,
                    relation_type=RELATION_TYPE.INSTANCE,
                    include_thing=False,
                ),
            )
            relation_candidates.extend(
                [
                    CandidateRelation(
                        entity=res.link.from_subject.label,
                        relation=res.link.label,
                        target=res.link.to_subject.label,
                        score=res.score,
                        link=res.link,
                    )
                    for res in top_results.results
                ]
            )

        for entity in erl.entities:
            top_results = self.guidance_man.search_fuzzy(
                query=FuzzyQuery(
                    q=f"A {entity.type}",
                    limit=candidate_limit,
                    type=RETURN_TYPE.SUBJECT,
                    relation_type=RELATION_TYPE.INSTANCE,
                    include_thing=False,
                )
            )
            candidates = [
                CandidateEntity(
                    type=res.subject.label,
                    score=res.score,
                    identifier=res.subject.label,
                    subject=res.subject,
                )
                for res in top_results.results
            ]
            candidate_ids = [c.subject.subject_id for c in candidates]
            entity_candidates.extend(candidates)
            for constraint in entity.constraints:
                top_results = self.guidance_man.search_fuzzy(
                    query=FuzzyQuery(
                        q=f"The {constraint.property} of is {constraint.modifier} {constraint.value}",
                        limit=candidate_limit,
                        from_id=candidate_ids,
                        type=RETURN_TYPE.LINK,
                        relation_type=RELATION_TYPE.PROPERTY,
                        include_thing=False,
                    )
                )
                constraint_candidates.extend(
                    [
                        CandidateConstraint(
                            property=res.link.label,
                            value=None,
                            modifier=None,
                            score=res.score,
                            type=res.link.to_proptype,
                            entity=res.link.from_subject.subject_id,
                            link=res.link,
                        )
                        for res in top_results.results
                    ]
                )
        candidates = Candidates(
            relations=relation_candidates,
            entities=entity_candidates,
            constraints=constraint_candidates,
        )
        return candidates

    def build_constrained_classes(self, candidates: Candidates) -> BaseModel:
        constrained_classes = []
        ALLOWED_ENTITY_TYPES = Enum(
            "ALLOWED_ENTITY_TYPES",
            {e.subject.subject_id: e.type for e in candidates.entities},
        )
        if len(candidates.entities) == 0:
            ALLOWED_ENTITY_TYPES = str

        ALLOWED_CONSTRAINT_TYPES = Enum(
            "ALLOWED_CONSTRAINT_TYPES",
            {c.link.property_id: c.property for c in candidates.constraints},
        )
        if len(candidates.constraints) == 0:
            ALLOWED_CONSTRAINT_TYPES = str

        ALLOWED_RELATION_TYPES = Enum(
            "ALLOWED_RELATION_TYPES",
            {r.link.property_id: r.relation for r in candidates.relations},
        )
        if len(candidates.relations) == 0:
            ALLOWED_RELATION_TYPES = str

        ConstrainedRelation = create_model(
            "ConstrainedRelation",
            # (BaseModel,),
            **{
                "entity": (str, ...),
                "relation": (ALLOWED_RELATION_TYPES, ...),
                "target": (str, ...),
            },
        )
        ConstrainedConstraint = create_model(
            "ConstrainedConstraint",
            # (BaseModel,),
            **{
                "property": (ALLOWED_CONSTRAINT_TYPES, ...),
                "value": (str, ...),
                "modifier": (str, ...),
            },
        )
        ConstrainedEntity = create_model(
            "ConstrainedEntity",
            # (BaseModel,),
            **{
                "type": (ALLOWED_ENTITY_TYPES, ...),
                "identifier": (str, ...),
                "constraints": (list[ConstrainedConstraint], []),
            },
        )
        ConstrainedEntitiesRelations = create_model(
            "ConstrainedEntitiesRelations",
            # (BaseModel,),
            **{
                "relations": (list[ConstrainedRelation], []),
                "entities": (list[ConstrainedEntity], []),
                "message": (str, "Constrained Entities and Relations"),
            },
        )

        return ConstrainedEntitiesRelations

    def enrich_entities_relations(
        self, erl: EntitiesRelations, candidates: Candidates
    ) -> EnrichedEntitiesRelations:
        with Session(self.guidance_man.engine) as session:
            session.execute(text("SET TRANSACTION READ ONLY"))
            session.autoflush = False

            def enrich_relation(relation: Relation) -> EnrichedRelation:
                value = (
                    relation.relation.value
                    if isinstance(relation.relation, Enum)
                    else relation.relation
                )
                link_db = session.execute(
                    select(SubjectLinkDB)
                    .where(
                        and_(
                            SubjectLinkDB.label == value,
                            SubjectLinkDB.property_id.in_(
                                [rel.link.property_id for rel in candidates.relations]
                            ),
                        )
                    )
                    .limit(1)
                ).first()
                return EnrichedRelation(
                    link=link_db[0].from_db(self.guidance_man.oman),
                    **relation.model_dump(),
                )

            def enrich_constraint(constraint: Constraint) -> EnrichedConstraint:
                value = (
                    constraint.property.value
                    if isinstance(constraint.property, Enum)
                    else constraint.property
                )
                link_db = session.execute(
                    select(SubjectLinkDB)
                    .where(
                        SubjectLinkDB.label == value,
                        SubjectLinkDB.property_id.in_(
                            [rel.link.property_id for rel in candidates.constraints]
                        ),
                    )
                    .limit(1)
                ).first()
                if link_db is None:
                    return None
                return EnrichedConstraint(
                    constraint=link_db[0].from_db(self.guidance_man.oman),
                    **constraint.model_dump(),
                )

            def enrich_entity(entity: Entity) -> EnrichedEntity:
                value = (
                    entity.type.value if isinstance(entity.type, Enum) else entity.type
                )
                subject_db = session.execute(
                    select(SubjectInDB)
                    .where(
                        SubjectInDB.label == value,
                        SubjectInDB.subject_id.in_(
                            [ent.subject.subject_id for ent in candidates.entities]
                        ),
                    )
                    .limit(1)
                ).first()
                constraints = [enrich_constraint(c) for c in entity.constraints]
                constraints = [c for c in constraints if c is not None]

                return EnrichedEntity(
                    subject=self.guidance_man.oman.enrich_subject(
                        subject_db[0].subject_id
                    ),
                    constraints=constraints,
                    **entity.model_dump(exclude=["constraints"]),
                )

            erl_enriched = EnrichedEntitiesRelations(
                relations=[enrich_relation(r) for r in erl.relations],
                entities=[enrich_entity(e) for e in erl.entities],
            )
            # swap links if the schema is the other way around - does not constrain llm
            # TODO: how could we constrain LLM?
            for relation in erl_enriched.relations:

                def get_entity_by_id(identifier: str):
                    return next(
                        (
                            e
                            for e in erl_enriched.entities
                            if e.identifier == identifier
                        ),
                        None,
                    )

                from_entity = get_entity_by_id(relation.entity)
                to_entity = get_entity_by_id(relation.target)
                if (
                    from_entity is not None
                    and from_entity.subject.is_of_type(relation.link.to_id)
                ) or (
                    to_entity is not None
                    and to_entity.subject.is_of_type(relation.link.from_id)
                ):
                    print(
                        f"Swapping relation {relation.relation} from {relation.entity} to {relation.target}"
                    )
                    # switch if either entity is not set and the relation is the other way around
                    relation.entity, relation.target = (
                        relation.target,
                        relation.entity,
                    )
                # add missing entities from the relation
                entities = [
                    (relation.entity, relation.link.from_id),
                    (relation.target, relation.link.to_id),
                ]
                for id, subject_id in entities:
                    entity = get_entity_by_id(id)
                    if entity is None:
                        # if we do not have the target entity, we create a the one from the relation
                        subject = session.execute(
                            select(SubjectInDB)
                            .where(
                                SubjectInDB.subject_id == subject_id,
                            )
                            .limit(1)
                        ).first()
                        if subject:
                            subject_parsed: Subject = subject[0].from_db(
                                self.guidance_man.oman
                            )
                            entity = EnrichedEntity(
                                identifier=id,
                                type=subject_parsed.label,
                                subject=subject_parsed,
                            )
                            erl_enriched.entities.append(entity)
            to_remove = []
            for entity in erl_enriched.entities:
                # remove orphan entities that are not in any relation
                relations_for_entity = [
                    e for e in erl_enriched.relations if e.entity == entity.identifier
                ] + [e for e in erl_enriched.relations if e.target == entity.identifier]
                if not len(relations_for_entity) > 0:
                    to_remove.append(entity)
            for entity in to_remove:
                erl_enriched.entities.remove(entity)
            # remove entities that are not
            return erl_enriched

    def initate(self, reset=True, config=None, force=True, *args, **kwargs):
        raise NotImplementedError(
            "LLMQuery does not support the initate method, use initiate() instead."
        )

    def initiate(self, force=False, n_queries=10, k_min=2, k_max=4):
        do_init = False
        if force:
            do_init = True
        else:
            with Session(self.guidance_man.engine) as session:
                count = session.execute(
                    select(func.count(SampledGraphDB.graph_id)).where(
                        SampledGraphDB.onto_hash == self.guidance_man.identifier
                    )
                ).scalar()
                if count == 0:
                    do_init = True
        if not do_init:
            return None
        rs = np.random.RandomState(42)
        k_s = rs.randint(k_min, k_max, n_queries)
        queries: list[tuple[str, EnrichedEntitiesRelations]] = []
        for i, k in enumerate(tqdm.tqdm(k_s)):
            query_graph = choose_graph(k, topic_man=self.guidance_man, seed=i, top_k=10)
            query_graph_reduced = reduce_erl(query_graph)
            query_response = self.guidance_man.llama_model.create_chat_completion(
                # grammar=self.grammar_erl,
                messages=[
                    {
                        "role": "system",
                        "content": ERL_PROMPT_QUERY_GEN,
                    },
                    {
                        "role": "user",
                        "content": ERL_PROMPT_EXAMPLE[1],
                    },
                    {
                        "role": "assistant",
                        "content": ERL_PROMPT_EXAMPLE[0],
                    },
                    {
                        "role": "user",
                        "content": query_graph_reduced.model_dump_json(),
                    },
                ],
                max_tokens=4096,
                temperature=0.3,  # get wild :)
            )
            query_str = query_response["choices"][0]["message"]["content"]
            queries.append((query_str, query_graph))

        BasePostgres.metadata.create_all(self.guidance_man.engine, checkfirst=True)
        with Session(self.guidance_man.engine) as session:
            # session.execute(text("SET TRANSACTION READ ONLY"))
            session.autoflush = True

            for query_str, query_graph in queries:
                sampled_graph = SampledGraphDB(
                    graph_name=f"k={len(query_graph.entities)}",
                    graph_query=query_str,
                    onto_hash=self.guidance_man.identifier,
                    instance_count=-1,
                )
                subject_ids = [e.subject.subject_id for e in query_graph.entities]

                entities: dict[str, GraphEntityDB] = {}

                for subject_id in subject_ids:
                    subject_link = session.execute(
                        select(SubjectInDB)
                        .where(SubjectInDB.subject_id == subject_id)
                        .limit(1)
                    ).first()
                    if subject_link:
                        entity = GraphEntityDB(
                            subject_id=subject_link[0].subject_id,
                        )
                        entity.graph = sampled_graph
                        entities[subject_id] = entity
                        session.add(entity)
                links: dict[int, SubjectLinkDB] = {}
                for rel in query_graph.relations:
                    link = GraphLinkDB(
                        subject_link_id=rel.link.link_id,
                    )
                    link.graph = sampled_graph
                    from_entity = entities[rel.link.from_id]
                    to_entity = entities[rel.link.to_id]

                    link.from_entity = from_entity
                    link.to_entity = to_entity
                    links[rel.link.link_id] = link
                    session.add(link)
                session.add(sampled_graph)
                session.commit()
        return queries

    def get_examples(self, n=10) -> list[EnrichedEntitiesRelations]:
        with Session(self.guidance_man.engine) as sess:
            graphs = (
                sess.query(SampledGraphDB)
                .filter(SampledGraphDB.onto_hash == self.guidance_man.identifier)
                .all()
            )
            examples = []
            for graph in graphs:
                query_graph = EnrichedEntitiesRelations(message=graph.graph_query)
                for entity in graph.graph_entities:
                    enriched_entity = EnrichedEntity(
                        identifier=f"{escape_sparql_var(entity.subject.subject_id)}_{entity.entity_id}",
                        constraints=[],
                        type=entity.subject.subject_id,
                        subject=self.guidance_man.oman.enrich_subject(
                            entity.subject.subject_id
                        ),
                    )
                    query_graph.entities.append(enriched_entity)
                for link in graph.graph_links:
                    enriched_relation = EnrichedRelation(
                        entity=f"{escape_sparql_var(link.from_entity.subject.subject_id)}_{link.from_entity.entity_id}",
                        relation=link.subject_link.property_id,
                        target=f"{escape_sparql_var(link.to_entity.subject.subject_id)}_{link.to_entity.entity_id}",
                        link=link.subject_link.from_db(self.guidance_man.oman),
                    )
                    query_graph.relations.append(enriched_relation)
                examples.append(query_graph)
            return examples
