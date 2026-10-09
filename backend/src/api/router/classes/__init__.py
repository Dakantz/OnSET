from fastapi import (
    APIRouter,
    Query,
    Body,
)


from api.config import DEFAULT_MANMAN
from model import GeneralizationQuery, SparseOutLinks, Subject, SubjectLink
from explorative.exp_model import (
    SubjectLinkDB,
    FuzzyQuery,
    FuzzyQueryResults,
)
from sqlalchemy.orm import Session

from api.router.classes.search import search_router
from api.router.classes.instances import instances_router


manman = DEFAULT_MANMAN

classes_router = APIRouter(prefix="/classes")
classes_router.include_router(search_router)
classes_router.include_router(instances_router)


@classes_router.get("/outlinks")
def get_outlinks(subject_id: str = Query()) -> SparseOutLinks:
    if not hasattr(manman.dataset_manager, "engine"):
        manman.dataset_manager.initialise(
            glob_path=f"{manman.base_path}/datasets/ALS/**/*.csv"
        )
    return manman.dataset_manager.target_outlinks(subject_id)


@classes_router.get("/subjects")
def get_subject(
    subject_id: str = Query(),
) -> Subject | None:
    return manman.ontology_manager.enrich_subject(subject_id)


@classes_router.get("/links")
def get_link(
    link_id: str = Query(),
) -> SubjectLink | None:
    with Session(manman.guidance_man.engine) as session:
        link = (
            session.query(SubjectLinkDB)
            .filter(SubjectLinkDB.property_id == link_id)
            .first()
        )
        if link is None:
            return None
        return link.from_db(oman=manman.ontology_manager)


@classes_router.get("/relations")
def get_relations(
    q: str | None = Query(None),
    from_id: str | None = Query(None),
    to_id: str | None = Query(None),
) -> list[SubjectLink]:
    return manman.guidance_man.search_links(q, from_id, to_id)


@classes_router.get("/full")
def get_full_classes() -> list[Subject]:
    roots = manman.ontology_manager.get_full_classes()
    return roots


@classes_router.get("/roots")
def get_root_classes() -> list[Subject]:
    return manman.ontology_manager.get_root_classes()


@classes_router.get("/subclasses")
def get_class(cls: str = Query()) -> list[Subject]:
    return manman.ontology_manager.get_subclasses(cls)


@classes_router.post("/subclasses/search")
def get_class_search(q: FuzzyQuery = Body(FuzzyQuery())) -> FuzzyQueryResults:
    return manman.guidance_man.search_subclasses(q)


@classes_router.post("/parents/most_generic")
def get_most_generics(
    q: GeneralizationQuery = Body(GeneralizationQuery()),
) -> Subject:
    return manman.ontology_manager.get_most_generic_classes(q)
