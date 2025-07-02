# %%
import numpy as np

# %%
import sys
import os

sys.path.insert(0, os.path.abspath("../.."))
sys.path.append(os.path.abspath("../../backend"))
sys.path.append(os.path.abspath(""))

import networkx as nx

from langchain_core.prompts import ChatPromptTemplate
from typing import TypeVar
from sqlalchemy.orm import aliased
from sqlalchemy.sql import text
from rdflib.plugins.stores.sparqlstore import SPARQLStore
from backend.model import Session, Subject, SubjectLink

from backend.ontology import OntologyManager, OntologyConfig, Graph
from backend.explorative.explorative_support import GuidanceManager, select
from backend.explorative.llm_query import (
    Entity,
    Relation,
    EntitiesRelations,
    EnrichedEntity,
    EnrichedRelation,
    EnrichedEntitiesRelations,
    SubjectInDB,
    SubjectLinkDB,
)
from backend.explorative.llm_query_gen import (
    choose_graph,
    reduce_erl,
    erl_to_templated_query,
)
import argparse
from tqdm import tqdm
import pandas as pd

# %%
from backend.eval_config import (
    DBPEDIA_CONFIGS,
    OMA_CONFIGS,
    UNIPROT_CONFIGS,
    DNB_CONFIGS,
    BTO_CONFIGS,
    YAGO_CONFIGS,
    EvalConfig,
)

db_setups = [
    DBPEDIA_CONFIGS[-1],
    UNIPROT_CONFIGS[-1],
    BTO_CONFIGS[-1],
    # DNB_CONFIGS[-1],
    YAGO_CONFIGS[-1],
]
# db_setups = [BTO_CONFIGS[0]]


parser = argparse.ArgumentParser()
parser.add_argument(
    "--dataset", type=int, choices=list(range(len(db_setups))), default=0
)
# %%
top_k = 100
seed = 42

# %%

SL = TypeVar("SL")


class EnrichedDBEntity(Entity, arbitrary_types_allowed=True):
    subject: SubjectInDB | Subject | None


class EnrichedDBRelation(Relation, arbitrary_types_allowed=True):
    link: SubjectLinkDB | SubjectLink | None


messages = [
    {
        "role": "system",
        "content": """"You are a helpful assistant turning relational knowledge into natural language.""",
    },
    {
        "role": "user",
        "content": EntitiesRelations(
            entities=[
                Entity(
                    identifier="person 1",
                    type="person",
                ),
                Entity(
                    identifier="place 1",
                    type="place",
                ),
                Entity(
                    identifier="company 1",
                    type="person",
                ),
            ],
            relations=[
                Relation(
                    entity="company 1",
                    relation="employs",
                    target="person 1",
                ),
                Relation(
                    entity="person 1",
                    relation="residence",
                    target="place 1",
                ),
            ],
        ).model_dump_json(),
    },
    {
        "role": "assistant",
        "content": "a person is employed by a company and the same person resides in a place",
    },
]


if __name__ == "__main__":
    # %%

    args = parser.parse_args()
    setup: EvalConfig = db_setups[args.dataset]
    print("Generating for ", setup.name)
    store = SPARQLStore(
        setup.sparql_endpoint,
        method="POST_FORM",
        params={"infer": False, "sameAs": False},
    )
    graph = Graph(store=store)

    config = OntologyConfig()

    ontology_manager = OntologyManager(config, graph)
    guidance_man = GuidanceManager(
        ontology_manager,
        llm_model_id=setup.model_id,
        conn_str=setup.conn_str,
    )
    llama_model = guidance_man.llama_model

    # %%

    # %%
    n_examples = 128
    n_nodes = [2, 3, 5, 7]
    resulting_examples = []
    progress = tqdm(total=n_examples * len(n_nodes))
    for n_node in n_nodes:
        for i in range(n_examples):
            try:
                erl = choose_graph(seed=i, max_nodes=n_node, guidance_man=guidance_man)
                correct_n_nodes = len(erl.entities)
                reduced_erl = reduce_erl(erl)
                response = llama_model.create_chat_completion(
                    # grammar=self.grammar_erl,
                    messages=messages
                    + [
                        {
                            "role": "user",
                            "content": reduced_erl.model_dump_json(),
                        }
                    ],
                    max_tokens=4096,
                    temperature=0.3,
                )
                templated_query = erl_to_templated_query(erl)
                progress.update(1)
                resulting_examples.append(
                    {
                        "generator": "llama",
                        "response": response["choices"][0]["message"]["content"],
                        "n_nodes": correct_n_nodes,
                        "seed": i,
                        "erl": erl.model_dump_json(),
                    }
                )
                resulting_examples.append(
                    {
                        "generator": "templated",
                        "response": templated_query,
                        "n_nodes": correct_n_nodes,
                        "seed": i,
                        "erl": erl.model_dump_json(),
                    }
                )
                resulting_examples_df = pd.DataFrame(resulting_examples)
                # only save unique examples
                resulting_examples_df = resulting_examples_df.drop_duplicates(
                    subset=["erl", "generator", "response"]
                )
                resulting_examples_df.to_csv(f"examples/examples_{setup.name}.csv")
            except Exception as e:
                print(e)
                continue

    # %%

    # %% [markdown]
    #
    print("Done generating examples", setup.name)
