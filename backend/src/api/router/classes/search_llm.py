from fastapi import (
    APIRouter,
    Query,
    BackgroundTasks,
)

from api.config import DEFAULT_MANMAN
from explorative.llm_query import QueryProgress, EnrichedEntitiesRelations


manman = DEFAULT_MANMAN

search_llm_router = APIRouter(prefix="/llm")


@search_llm_router.get("")
def get_llm_results(
    background_tasks: BackgroundTasks,
    q: str = Query("working field of person"),
) -> QueryProgress:
    return manman.llm_query.start_query(q, background_tasks)


@search_llm_router.get("/running")
def get_llm_results_running(
    query_id: str = Query(),
) -> QueryProgress | None:
    return manman.llm_query.query_progress(query_id)


@search_llm_router.get("/examples")
def get_llm_examples() -> list[EnrichedEntitiesRelations]:
    return manman.llm_query.get_examples()
