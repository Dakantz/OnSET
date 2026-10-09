from fastapi.middleware.cors import CORSMiddleware

from typing import Any
from rdflib.plugins.stores.sparqlstore import SPARQLStore

from ontology import OntologyManager, OntologyConfig, Graph, InstanceQuery
from datasetmatcher import DatasetManager
from explorative.explorative_support import GuidanceManager
from explorative.exp_model import (
    SparqlQuery,
    Topic,
    SubjectLinkDB,
    FuzzyQuery,
    FuzzyQueryResults,
)
from explorative.llm_query import LLMQuery, QueryProgress, EnrichedEntitiesRelations
from eval_config import (
    BTO_CONFIGS,
    DBPEDIA_CONFIGS,
    UNIPROT_CONFIGS,
    DNB_CONFIGS,
    GUTBRAINIE_CONFIGS,
    ALL_CONFIG_MAP,
)
from initiator import InitatorManager
from assistant.model import QueryGraph, Operations
from assistant.iterative_assistant import IterativeAssistant
from redis_cache import RedisCache
from sqlalchemy.orm import Session

from sklearn.manifold import TSNE, MDS
from sklearn.decomposition import PCA
import numpy as np
import os


base_path = "../../data"
onto_path = f"{base_path}/hero-ontology/hereditary_clinical.ttl"


class ManMan:
    def __init__(self, config_name: str = "dbpedia", idx: int = -1):
        self.db_config = None
        self.config_name = config_name
        self.idx = idx

        db_config = ALL_CONFIG_MAP[config_name][idx]
        # db_config = GUTBRAINIE_CONFIGS[1]

        db_config.conn_str = os.getenv("DB_CONN_STR", db_config.conn_str)
        db_config.sparql_endpoint = os.getenv(
            "SPARQL_ENDPOINT", db_config.sparql_endpoint
        )
        db_config.model_id = os.getenv("LLM_MODEL_ID", db_config.model_id)
        db_config.model_quant = os.getenv("LLM_MODEL_QUANT", db_config.model_quant)
        db_config.redis_cache_url = os.getenv(
            "REDIS_CACHE_URL", db_config.redis_cache_url
        )
        print("Using DB config:", db_config)
        self.db_config = db_config

        self.base_path = base_path
        self.onto_path = onto_path
        self.start_systems()

    def start_systems(self):
        db_config = self.db_config
        self.store = SPARQLStore(
            db_config.sparql_endpoint,
            method="POST_FORM",
            params={"infer": False, "sameAs": False},
            timeout=300,
        )
        # store = SPARQLStore(
        #     "http://examode.dei.unipd.it:7200/repositories/TUGraz_test",
        #     method="POST_FORM",
        #     params={"infer": False, "sameAs": False},
        #     headers={
        #         "Authorization": "GDB eyJ1c2VybmFtZSI6ImJlbmVkaWt0LmthbnR6IiwiYXV0aGVudGljYXRlZEF0IjoxNzMzODMxOTk3NTIzfQ==.QqebiiJt752/OThRujrJyNg0XXKrrteU7MhNPUCoSBI="
        #     },
        # )
        self.graph = Graph(store=self.store)

        self.config = OntologyConfig()
        self.config.encoding_model = db_config.encoding_model
        self.config.ontology_extension = db_config.ontology_extension
        self.ontology_manager = OntologyManager(self.config, self.graph)
        self.dataset_manager = DatasetManager(self.ontology_manager)
        # dataset_manager.initialise(glob_path="data/datasets/ALS/**/*.csv")

        # ontology_manager.load_full_graph()

        self.guidance_man = GuidanceManager(
            self.ontology_manager,
            conn_str=db_config.conn_str,
            llm_model_id=db_config.model_id,
        )
        # topic_man.initialize_topics(force=False)

        self.llm_query = LLMQuery(
            topic=self.guidance_man, redis_url=db_config.redis_cache_url
        )

        self.initatior = InitatorManager()
        self.initatior.register(self.guidance_man)
        self.initatior.register(self.llm_query)

        self.iterative_assistant = IterativeAssistant(guidance=self.guidance_man)

        self.assistant_cache = RedisCache(
            redis_url=db_config.redis_cache_url,
            model=Operations,
        )


DEFAULT_MANMAN = ManMan()
