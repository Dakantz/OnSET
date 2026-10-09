from fastapi import (
    APIRouter,
    Query,
)

from api.config import DEFAULT_MANMAN
from model import Instance, Property, Subject
from ontology import InstanceQuery


manman = DEFAULT_MANMAN

instances_router = APIRouter(prefix="/instances")


@instances_router.get("")
def get_named_instance(cls: str = Query()) -> list[Subject]:
    return manman.ontology_manager.get_named_individuals(cls)


@instances_router.get("/search")
def get_named_instance_search(query: InstanceQuery = Query()) -> list[Instance]:
    return manman.ontology_manager.get_instances(query)


@instances_router.get("/properties")
def get_named_instance_properties(instance_id: str = Query()) -> dict[str, Property]:
    return manman.ontology_manager.outgoing_edges_for(instance_id)
