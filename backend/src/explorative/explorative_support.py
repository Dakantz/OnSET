from __future__ import annotations
from tkinter import Image
from sentence_transformers import SentenceTransformer
import torch
from langchain_core.language_models import LLM
from llama_cpp import Llama
from hashlib import sha256
import regex as re
from sqlalchemy import create_engine, select, delete, or_
from sqlalchemy.orm import Session
from tqdm import tqdm
import pandas as pd

from explorative.data_tensor import DataTensor
from model import SubjectLink
from ontology import OntologyManager

from explorative.exp_model import (
    BasePostgres,
    TopicDB,
    SubjectLinkDB,
    SubjectInDB,
    FuzzyQueryResult,
    FuzzyQuery,
    N_EMBEDDINGS,
    RETURN_TYPE,
    RELATION_TYPE,
    FUZZY_QUERY_ORDER,
    FuzzyQueryResults,
    Topic,
)


class GuidanceManager:
    def __init__(
        self,
        oman: OntologyManager,
        device=None,
        conn_str: str = "postgresql+psycopg://postgres:postgres@localhost:5434/onset",
        llm_model_id: str = "NousResearch/Hermes-3-Llama-3.1-8B-GGUF",
        llm_quant_model: str = "*.Q8_0.gguf",
        langchain_model: LLM = None,
        ctx_size=10000,
    ) -> None:
        self.oman = oman
        if device is None:
            if torch.cuda.is_available():
                device = "cuda"
            elif torch.mps.is_available():
                device = "mps"
            else:
                device = "cpu"
        print("Using device", device)
        self.device = device
        self._encoding_model = None
        # This model supports two prompts: "s2p_query" and "s2s_query" for sentence-to-passage and sentence-to-sentence tasks, respectively.
        # They are defined in `config_sentence_transformers.json`
        self.query_prompt_name = "s2p_query"
        self.llm_model_id = llm_model_id
        self.llm_quant_model = llm_quant_model
        self.langchain_model = langchain_model
        self.ctx_size = ctx_size
        self.engine = create_engine(conn_str)
        identifier_results = self.oman.onto.query(
            "SELECT ?s  ?p ?o WHERE {?s ?o ?p.} LIMIT 25"
        )
        if len(identifier_results) == 1:
            raise ValueError(
                "Ontology is empty or SPARQL endpoint is not reachable",
                identifier_results,
            )
        self.identifier = sha256(
            ".".join([str(e) for e in identifier_results]).encode()
        ).hexdigest()
        self.__lama_model = None
        self.__embedding_model = None

    @property
    def llama_model(self) -> Llama:
        if self.__lama_model is not None:
            return self.__lama_model
        print("Loading LLM model", self.llm_model_id, self.langchain_model)
        if self.llm_model_id is None and self.langchain_model is None:
            raise ValueError("No LLM model id specified")

        if self.langchain_model is not None:
            self.__lama_model = self.langchain_model
        elif self.llm_model_id is not None:
            self.__lama_model = Llama.from_pretrained(
                repo_id=self.llm_model_id,
                filename=self.llm_quant_model,
                n_batch=2048,
                n_ubatch=512,
                n_ctx=self.ctx_size,
                n_gpu_layers=-1,
                n_threads=6,
                embedding=False,
                temperature=0.6,
            )
        return self.__lama_model

    @property
    def embedding_model(self):
        if self.__embedding_model is not None:
            return self.__embedding_model
        self.__embedding_model = SentenceTransformer(
            "dunzhang/stella_en_400M_v5",
            trust_remote_code=True,
            config_kwargs={
                "use_memory_efficient_attention": False,
                "unpad_inputs": False,
            },
            revision="eb1ce34a33908596b61c83a88903b5f5f30beaa9",  # problematic merge, wrong dimensionality,
            device=self.device,
        )
        # self.embedding_model = SentenceTransformer(
        #     "paraphrase-MiniLM-L6-v2",
        # ).to(device)
        return self.__embedding_model

    def get_topic_tree(self) -> list[Topic]:
        with Session(self.engine) as session:
            root_topic = session.execute(
                select(TopicDB).where(
                    TopicDB.parent_topic_id == None,
                    TopicDB.onto_hash == self.identifier,
                    TopicDB.topic_id != -1,
                )
            ).first()

            def topic_tree(topic: TopicDB):
                return Topic(
                    topic_id=topic.topic_id,
                    topic=topic.topic,
                    count=topic.count,
                    parent_topic_id=topic.parent_topic_id,
                    # embedding=topic.embedding,
                    sub_topics=[
                        topic_tree(sub_topic) for sub_topic in topic.sub_topics
                    ],
                    subjects_ids=[s.subject_id for s in topic.subjects],
                    property_ids=[l.property_id for l in topic.links],
                )

            if root_topic is None:
                raise ValueError("No root topic found")
            return topic_tree(root_topic[0])

    def search_free(
        self,
        query: str,
        limit=25,
    ):
        query_embedding = self.embedding_model.encode(query)
        with Session(self.engine) as session:
            subjects = session.execute(
                select(SubjectInDB)
                .where(SubjectInDB.onto_hash == self.identifier)
                .order_by(SubjectInDB.embedding.cosine_distance(query_embedding))
                .limit(limit)
            ).all()
            subjects_enriched = [
                self.oman.enrich_subject(s[0].subject_id) for s in subjects
            ]
            links = session.execute(
                select(SubjectLinkDB)
                .where(SubjectLinkDB.onto_hash == self.identifier)
                .order_by(SubjectLinkDB.embedding.cosine_distance(query_embedding))
                .limit(limit)
            ).all()
            links_enriched = [l[0].from_db(self.oman) for l in links]
            return FuzzyQueryResults(
                links=links_enriched,
                subjects=subjects_enriched,
            )

    def search_links(
        self, querystring: str = None, from_id: str = None, to_id: str = None
    ):
        with Session(self.engine) as session:
            query = select(SubjectLinkDB).where(
                SubjectLinkDB.onto_hash == self.identifier
            )
            if from_id is not None:
                query = query.where(SubjectLinkDB.from_id == from_id)
            if to_id is not None:
                query = query.where(SubjectLinkDB.to_id == to_id)
            if querystring is not None:
                query_embedding = self.embedding_model.encode(querystring)
                query = query.order_by(
                    SubjectLinkDB.embedding.cosine_distance(query_embedding)
                )
            links = session.execute(query.limit(25)).all()
            links_enriched = [l[0].from_db(self.oman) for l in links]
            return links_enriched

    def __embed_query(
        self,
        query: FuzzyQuery,
        session: Session,
    ):
        query_embedding = None
        if query.q is not None and len(query.q) > 0:
            query_embedding = self.embedding_model.encode(
                query.q, prompt_name=self.query_prompt_name
            )
        if query.topic_ids is not None and len(query.topic_ids) > 0:
            topics = session.execute(
                select(TopicDB)
                .where(TopicDB.onto_hash == self.identifier)
                .where(TopicDB.topic_id.in_(query.topic_ids))
            ).all()
            topic_embeddings = torch.tensor([topic[0].embedding for topic in topics])
            topic_embedding = torch.mean(topic_embeddings, axis=0)
            if query_embedding is not None:
                query_embedding = (
                    1 - query.mix_topic_factor
                ) * query_embedding + query.mix_topic_factor * topic_embedding
            else:
                query_embedding = topic_embedding

        if query.q is None and (query.topic_ids is None or len(query.topic_ids) == 0):
            query_embedding = (
                torch.ones(N_EMBEDDINGS) / N_EMBEDDINGS
            )  # default to uniform
        return query_embedding

    def search_fuzzy(self, query: FuzzyQuery):
        with Session(self.engine) as session:
            query_embedding = self.__embed_query(query, session)

            results: list[FuzzyQueryResult] = []
            if query.type == RETURN_TYPE.SUBJECT or query.type == RETURN_TYPE.BOTH:
                order_by = (
                    SubjectInDB.embedding.cosine_distance(query_embedding)
                    if query.order == FUZZY_QUERY_ORDER.SCORE
                    else SubjectInDB.instance_count
                )
                query_subject = (
                    select(
                        SubjectInDB,
                        SubjectInDB.embedding.cosine_distance(query_embedding).label(
                            "distance"
                        ),
                    )
                    .where(SubjectInDB.onto_hash == self.identifier)
                    .order_by(order_by)
                    .offset(query.skip)
                    .limit(query.limit)
                )
                if query.entity_type is not None:
                    query_subject = query_subject.where(
                        SubjectInDB.subject_type == query.entity_type
                    )
                subjects = session.execute(query_subject).all()
                subjects_enriched = [
                    (self.oman.enrich_subject(s[0].subject_id), s.distance)
                    for s in subjects
                ]
                for s in subjects_enriched:
                    results.append(FuzzyQueryResult(subject=s[0], score=s[1]))
            if query.type == RETURN_TYPE.LINK or query.type == RETURN_TYPE.BOTH:
                order_by = (
                    SubjectLinkDB.embedding.cosine_distance(query_embedding)
                    if query.order == FUZZY_QUERY_ORDER.SCORE
                    else SubjectLinkDB.instance_count
                )
                query_link = select(
                    SubjectLinkDB,
                    SubjectLinkDB.embedding.cosine_distance(query_embedding).label(
                        "distance"
                    ),
                ).where(SubjectLinkDB.onto_hash == self.identifier)
                if query.from_id is not None:
                    if isinstance(query.from_id, str):
                        query.from_id = [query.from_id]
                    from_parents = [
                        self.oman.get_parents(from_id) + [from_id]
                        for from_id in query.from_id
                    ]
                    from_parents = [
                        item for sublist in from_parents for item in sublist
                    ]
                    if query.include_thing:
                        from_parents.append("owl:Thing")
                    query_link = query_link.where(
                        SubjectLinkDB.from_id.in_(from_parents),
                    )
                if query.to_id is not None:
                    to_parents = self.oman.get_parents(query.to_id) + [query.to_id]
                    if query.include_thing:
                        to_parents.append("owl:Thing")
                    query_link = query_link.where(SubjectLinkDB.to_id.in_(to_parents))
                if query.relation_type == RELATION_TYPE.INSTANCE:
                    query_link = query_link.where(
                        SubjectLinkDB.to_id != None,
                    )
                elif query.relation_type == RELATION_TYPE.PROPERTY:
                    query_link = query_link.where(
                        SubjectLinkDB.to_id == None,
                        SubjectLinkDB.to_proptype
                        != None,  # constraint to known proptypes
                    )
                query_link = query_link.order_by(order_by)
                links = session.execute(
                    query_link.offset(query.skip).limit(query.limit)
                ).all()

                links_enriched = [(l[0].from_db(self.oman), l.distance) for l in links]

                for l in links_enriched:
                    results.append(
                        FuzzyQueryResult(
                            link=l[0], score=l[1] if l[1] is not None else 0.0
                        )
                    )
            results = sorted(results, key=lambda x: x.score, reverse=False)
            return FuzzyQueryResults(results=results)

    def search_subclasses(self, query: FuzzyQuery):
        with Session(self.engine) as session:
            query_embedding = self.__embed_query(query, session)
            results: list[FuzzyQueryResult] = []
            subclasses = self.oman.get_all_subclasses(query.from_id)
            # rerank by embedding
            query = (
                select(
                    SubjectInDB,
                    SubjectInDB.embedding.cosine_distance(query_embedding).label(
                        "distance"
                    ),
                )
                .where(
                    SubjectInDB.onto_hash == self.identifier,
                    SubjectInDB.subject_id.in_(
                        [s.subject_id for s in subclasses],
                    ),
                )
                .order_by(SubjectInDB.embedding.cosine_distance(query_embedding))
            )
            results = session.execute(query).all()
            results = [
                FuzzyQueryResult(
                    subject=self.oman.enrich_subject(s[0].subject_id),
                    score=s.distance if s.distance is not None else 0.0,
                )
                for s in results
            ]
            return FuzzyQueryResults(results=results)

    @property
    def encoding_model(self):
        if self._encoding_model is None:
            self._encoding_model = SentenceTransformer(self.oman.config.encoding_model)
        return self._encoding_model

    def encode(self, text: str | None = None, image: Image | None = None):
        assert text is not None or image is not None, (
            "Either text or image must be provided"
        )
        out = self.encoding_model.encode(
            [text if text is not None else image], convert_to_numpy=True
        )[0]
        dt = DataTensor.from_numpy(out)
        return dt
