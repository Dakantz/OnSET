import sys
import os

sys.path.insert(0, os.path.abspath("../.."))
sys.path.append(os.path.abspath("../../backend/src"))
sys.path.append(os.path.abspath(""))

from rdflib.plugins.stores.sparqlstore import SPARQLStore

from ontology import OntologyManager, OntologyConfig, Graph
from datasetmatcher import DatasetManager
from explorative.explorative_support import GuidanceManager
from explorative.topic_init import TopicInitator
from explorative.llm_query import (
    EnrichedEntitiesRelations,
    LLMQuery,
    QueryProgress,
)
import argparse
from tqdm import tqdm
import pandas as pd

# %%
from eval_config import (
    DBPEDIA_CONFIGS,
    OMA_CONFIGS,
    UNIPROT_CONFIGS,
    BTO_CONFIGS,
    DNB_CONFIGS,
    YAGO_CONFIGS,
    GUTBRAINIE_CONFIGS,
    DBLP_CONFIGS,
    ALL_CONFIG_MAP,
    EvalConfig,
)

db_setups = [
    # OLYMPICS_CONFIGS[-1],
    DBPEDIA_CONFIGS[-1],
    UNIPROT_CONFIGS[-1],
    BTO_CONFIGS[-1],
    DNB_CONFIGS[-1],
    YAGO_CONFIGS[-1],
    GUTBRAINIE_CONFIGS[-1],
    DBLP_CONFIGS[-1],
]
# db_setups = []


parser = argparse.ArgumentParser()
parser.add_argument(
    "--dataset-id",
    type=int,
    choices=list(range(len(db_setups))),
    default=None,
)
parser.add_argument("--dataset", type=str, choices=list(ALL_CONFIG_MAP.keys()))
if __name__ == "__main__":
    print("Starting")
    # %%
    args = parser.parse_args()
    setup: EvalConfig = (
        db_setups[args.dataset_id]
        if args.dataset_id is not None
        else ALL_CONFIG_MAP[args.dataset][-1]
    )
    print("Setup for ", setup.name)
    store = SPARQLStore(
        setup.sparql_endpoint,
        method="POST_FORM",
        params={"infer": False, "sameAs": False},
        retries=10,
    )
    graph = Graph(store=store)

    config = OntologyConfig()
    config.ontology_extension = setup.ontology_extension
    config.encoding_model = setup.encoding_model

    ontology_manager = OntologyManager(config, graph)
    dataset_manager = DatasetManager(ontology_manager)
    dataset_manager.initialise(glob_path="data/datasets/ALS/**/*.csv")
    guidance_manager = GuidanceManager(
        ontology_manager, conn_str=setup.conn_str, llm_model_id=setup.model_id
    )
    initiator = TopicInitator(guidance_manager)
    llm_man = LLMQuery(guidance_manager)
    guidance_manager.llama_model
    print(guidance_manager.identifier)
    initiator.initate(force=True, delete_tables=True)
    llm_man.initiate(force=True)

    print("Database initialised with setup:", setup.name)
# %%
