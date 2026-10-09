from hashlib import sha512
from ontology import OntologyManager
import pandas as pd
import numpy as np
from sentence_transformers import SentenceTransformer
from glob import glob
from sklearn.feature_extraction.text import TfidfVectorizer
import tqdm
from PIL.Image import Image
from sqlalchemy import create_engine, select
from sqlalchemy.orm import (
    Session,
    lazyload,
)

from model import (
    Base,
    Subject,
    MatchDB,
    PathElementDB,
    RelationsFoundDB,
    RelationsFound,
    OutLink,
    SparseOutLinks,
)

from utils import to_readable_camelcase


def is_postive(series: pd.Series):  # TODO improve positive check?
    if series.dtype == "bool":
        return series
    elif series.dtype == "object":
        return series.notnull() & (series != "")
    else:
        return series.notna() & (series > 0)


def unwrap_idx(idx: str):
    return int(idx.split("-")[0]), int(idx.split("-")[1])


class DataSetRepresentation:
    def __init__(
        self, path: str, index_col: str | int = 0, mngr: "DatasetManager" = None
    ):
        self.paths = [path]
        self.df = pd.read_csv(path, index_col=index_col)
        if self.df.shape[1] == 0:
            self.df = pd.read_csv(path, index_col=index_col, sep=";")
        self.columns = self.df.columns.tolist()
        self.columns_embedding: list[np.ndarray] = None
        self.mngr = mngr

    def expand_categorical(self):
        self.unique_counts = self.df.nunique()
        self.categorical_columns = self.df.columns[
            (self.unique_counts / len(self.df) < 0.3)
            & (self.unique_counts > 1)
            & (self.unique_counts < 512)
            & (self.df.dtypes == "object")
        ].to_list()
        self.df = pd.get_dummies(self.df, columns=self.categorical_columns)

    def merge(self, other: "DataSetRepresentation"):
        if other.df.shape[1] > 0:
            self.df = pd.concat([self.df, other.df])
        self.columns = self.df.columns
        self.paths.append(other.paths)

    def col_id(self):
        return ",".join(self.df.columns.tolist())

    def cols_readable(self):
        index_name = self.df.index.name
        col_names_flipped = [
            f"{to_readable_camelcase(col)} {to_readable_camelcase(index_name)} {to_readable_camelcase(self.paths[0])}"
            for col in self.df.columns
        ]
        return col_names_flipped

    def embed_cols(self):
        columns_embedding = self.mngr.model.encode(self.cols_readable())
        self.columns_embedding = [
            columns_embedding[e, :] for e in range(columns_embedding.shape[0])
        ]
        return self.columns_embedding

    def tfidf_cols(self):
        columns_tfidf = self.mngr.vectorizer.transform(self.cols_readable()).toarray()
        self.columns_tfidf = [
            columns_tfidf[e, :] for e in range(columns_tfidf.shape[0])
        ]
        return self.columns_tfidf


class DatasetManager:
    def __init__(self, ontology_manager: OntologyManager):
        self.ontology_manager = ontology_manager
        # self.ontology_manager.get_full_classes()
        self.onto_relations: list[tuple[list[str], str]] = []
        self.all_relations: pd.DataFrame = None

    def initialise(self, glob_path: str = "data/**/*.csv"):
        self.__load_datasets_from_glob(glob_path)
        if self.representations is not None and len(self.representations) > 0:
            hash_merged = sha512(
                ("".join([rep.col_id() for rep in self.representations_merged])).encode(
                    "utf-8"
                )
            ).hexdigest()
            print("--> Trying to load from db", hash_merged)
            self.engine = create_engine(f"sqlite:///{hash_merged}.db")
            Base.metadata.create_all(self.engine)
            with Session(self.engine) as session:
                if session.query(RelationsFoundDB).count() == 0:
                    print("--> No data found, building from scratch")
                    self.vectorizer = TfidfVectorizer()
                    self.model = SentenceTransformer(
                        "sentence-transformers/all-MiniLM-L6-v2"
                    )
                    for rep in self.representations_merged:
                        rep.embed_cols()
                    self.load_relations()
                    self.__build_rankings()
                    self.__update_df_best_match()
                    self.__uniquify_rankings()
                    self.__filter_relations()
                    for i, row in self.all_relations_filtered.iterrows():
                        relation = RelationsFoundDB(
                            path=[PathElementDB(path=p) for p in row["path"]],
                            subject_id=row["subject_id"],
                            text=row["text"],
                        )
                        rankings: pd.DataFrame = row["rankings_moving"]
                        if rankings is None:
                            continue
                        rankings = rankings.sort_values(
                            "score", ascending=False
                        ).reset_index(drop=True)
                        for j, match in rankings.iterrows():
                            relation.matches.append(
                                MatchDB(
                                    colname=self.representations_merged[
                                        int(match["idx"].split("-")[0])
                                    ].df.columns[int(match["idx"].split("-")[1])],
                                    idx=match["idx"],
                                    score=match["score"],
                                    rank=j,
                                )
                            )
                        # relation.best_match = Match(
                        #     **row["rankings"].iloc[0].to_dict()
                        # )
                        session.add(relation)
                        session.commit()

                else:
                    print("--> Data found, loading from db")
                self.all_relations_loaded = session.query(RelationsFoundDB).all()

    def __get_relations(self, subj: Subject, path: list[str] = []):
        for prop_typ, props in subj.properties.items():
            for prop in props:
                self.onto_relations.append(
                    (path + [subj.label, prop.label], prop.subject_id)
                )

        for desc_typ, descs in subj.descendants.items():
            for desc in descs:
                if desc.subject_type != subj.subject_type:
                    self.onto_relations.append(
                        (
                            path + [subj.label, desc.label],
                            desc.subject_id,
                        )
                    )
                else:
                    self.__get_relations(desc, path=path + [subj.label])

    def load_relations(self):
        [
            self.__get_relations(root)
            for root in self.ontology_manager.get_full_classes()
        ]

        self.all_relations = pd.DataFrame(
            range(len(self.onto_relations)), columns=["id"]
        )
        self.all_relations["p_s"] = self.onto_relations
        self.all_relations["path"] = self.all_relations["p_s"].map(lambda x: x[0])
        self.all_relations["subject_id"] = self.all_relations["p_s"].map(lambda x: x[1])
        self.all_relations["text"] = self.all_relations["path"].map(
            lambda x: " ".join(x)
        )
        encoding = self.model.encode(self.all_relations["text"].values)

        self.all_relations["embeddings"] = [
            encoding[e, :] for e in range(encoding.shape[0])
        ]
        # self.all_relations.to_csv("all_relations.csv", index=False)

    def __load_datasets_from_glob(self, glob_path: str = "data/**/*.csv"):
        print("-- Loading and merging datasets")
        all_csvs = glob(glob_path, recursive=True)
        sorted(all_csvs)
        self.representations = [
            DataSetRepresentation(csv, mngr=self) for csv in all_csvs
        ]
        print(len(self.representations), "datasets loaded")
        mergeables: dict[str, list[DataSetRepresentation]] = {}
        for rep in self.representations:
            if rep.col_id() not in mergeables:
                mergeables[rep.col_id()] = []
            mergeables[rep.col_id()].append(rep)
        # for k, mergeable in mergeables.items():
        #     print(k, len(mergeable))
        for col_id, reps in mergeables.items():
            if len(reps) > 1:
                for rep in reps[1:]:
                    reps[0].merge(rep)
                mergeables[col_id] = reps[:1]
        self.representations_merged = [
            rep for reps in mergeables.values() for rep in reps
        ]

        for rep in self.representations_merged:
            # print(rep.df.shape)
            rep.expand_categorical()
            # rep.tfidf_cols()

    def __build_rankings(self):
        print("-- Building rankings")
        self.all_relations["rankings"] = self.all_relations["embeddings"].map(
            lambda x: {}
        )
        for i, relation in tqdm.tqdm(
            self.all_relations.iterrows(), total=self.all_relations.shape[0]
        ):
            relation_embedding = relation["embeddings"]
            rankings = []
            for r_idx, rep in enumerate(self.representations_merged):
                col_similarities = np.dot(
                    relation_embedding, np.array(rep.columns_embedding).T
                )
                rankings.extend(
                    [
                        (
                            f"{r_idx}-{i}",
                            col_similarities[i],
                        )
                        for i in range(len(col_similarities))
                    ]
                )
            ranking_sorted = pd.DataFrame(
                rankings, columns=["idx", "score"]
            ).sort_values("score", ascending=False)

            self.all_relations.at[i, "rankings"] = ranking_sorted
        self.all_relations["rankings_moving"] = self.all_relations["rankings"].copy()

    def __update_df_best_match(self):
        self.all_relations["best_match"] = self.all_relations["rankings_moving"].map(
            lambda x: x.iloc[0]
        )
        self.all_relations["best_match_colname"] = self.all_relations["best_match"].map(
            lambda x: self.representations_merged[
                int(x["idx"].split("-")[0])
            ].df.columns[int(x["idx"].split("-")[1])]
        )
        self.all_relations["best_match_score"] = self.all_relations["best_match"].map(
            lambda x: x["score"]
        )
        self.all_relations["best_match_idx"] = self.all_relations["best_match"].map(
            lambda x: x["idx"]
        )
        return self.all_relations

    def __uniquify_rankings(self):
        print("-- Uniquifying rankings")

        still_non_unique = True
        last_uniques = 0
        while still_non_unique:
            self.__update_df_best_match()
            uniques = self.all_relations["best_match_idx"].unique()
            print(
                len(uniques),
                self.all_relations[self.all_relations["best_match_idx"].notna()].shape[
                    0
                ],
            )
            if len(uniques) == last_uniques:
                still_non_unique = False
            last_uniques = len(uniques)
            for unique_idx in uniques:
                selection = self.all_relations[
                    self.all_relations["best_match_idx"] == unique_idx
                ]
                if selection.shape[0] > 1:
                    # used more than once - only keep highest scoring, move others to second
                    sorted_selection = selection.sort_values(
                        "best_match_score", ascending=False
                    )
                    following_idx = sorted_selection.index[1:]
                    self.all_relations.loc[following_idx, "rankings_moving"] = (
                        self.all_relations.loc[following_idx, "rankings_moving"].map(
                            lambda x: x[1:]
                        )
                    )
                    self.__update_df_best_match()

    def __filter_relations(self, threshold: float = 0.15):
        all_relations_filtered = self.all_relations.copy()
        all_relations_filtered_selection = all_relations_filtered[
            all_relations_filtered["rankings_moving"].map(lambda r: r.iloc[0]["score"])
            < threshold
        ]
        all_relations_filtered.loc[
            all_relations_filtered_selection.index, "best_match_colname"
        ] = None
        all_relations_filtered.loc[
            all_relations_filtered_selection.index, "best_match_score"
        ] = None
        all_relations_filtered.loc[
            all_relations_filtered_selection.index, "best_match_idx"
        ] = None
        all_relations_filtered.loc[
            all_relations_filtered_selection.index, "rankings"
        ] = None
        all_relations_filtered.loc[
            all_relations_filtered_selection.index, "rankings_moving"
        ] = None
        self.all_relations_filtered = all_relations_filtered

        # self.all_relations_filtered[
        #     [
        #         "path",
        #         "subject_id",
        #         "text",
        #         "best_match_colname",
        #         "best_match_score",
        #         "best_match_idx",
        #     ]
        # ].to_csv("all_relations_filtered.csv", index=False)

    def relation_row_to_relation_found(self, row: pd.Series, top_k=5):
        matches = []
        repr_idx, col_idx = unwrap_idx(row["best_match_idx"])
        for idx, match in row["rankings"].iloc[:top_k].iterrows():
            m_repr_idx, m_col_idx = unwrap_idx(match["idx"])
            m_repr = self.representations_merged[m_repr_idx]
            matches.append(
                MatchDB(
                    colname=m_repr.df.columns[m_col_idx],
                    idx=match["idx"],
                    score=match["score"],
                )
            )
        return RelationsFoundDB(
            path=row["path"],
            subject_id=row["subject_id"],
            text=row["text"],
            matches=matches,
        )

    def target_outlinks(
        self, target_id: str = "<http://data.europa.eu/esco/isco/C0>", top_k=1
    ):
        source_repr: RelationsFoundDB = None
        with Session(self.engine) as session:
            stmt = (
                select(RelationsFoundDB)
                .join(MatchDB.relationfound)
                .where(RelationsFoundDB.subject_id == target_id)
                .options(lazyload(RelationsFoundDB.matches.and_(MatchDB.rank < top_k)))
                .order_by(MatchDB.score.desc())
                .execution_options(populate_existing=True)
            )

            source_reprs = session.execute(stmt).first()
            if source_reprs is None or source_reprs[0] is None:
                return SparseOutLinks(
                    source=RelationsFound(
                        subject_id=target_id, text="No source found", matches=[]
                    )
                )
            source_repr = RelationsFound.from_db(source_reprs[0])
            sorted(source_repr.matches, key=lambda x: x.score, reverse=True)
            best_match = source_repr.matches[0]
            repr_idx, col_idx = unwrap_idx(best_match.idx)
            repr = self.representations_merged[repr_idx]
            outlinks = SparseOutLinks(source=source_repr)
            positive_instances = repr.df[is_postive(repr.df.iloc[:, col_idx])]
            print(
                "found",
                positive_instances.shape[0],
                "positive instances for",
                repr_idx,
                col_idx,
                source_repr.text,
            )
            for other_idx, other_col in enumerate(positive_instances.columns.to_list()):
                identifier = f"{repr_idx}-{other_idx}"
                if other_idx == col_idx:
                    continue  # skip self
                positive_others = positive_instances[
                    is_postive(positive_instances.iloc[:, other_idx])
                ]
                if positive_others.shape[0] > 0:
                    stmt = (
                        select(RelationsFoundDB)
                        .join(MatchDB.relationfound)
                        .where(
                            MatchDB.idx == identifier,
                            MatchDB.rank < top_k,
                            RelationsFoundDB.subject_id != target_id,
                        )
                        .options(
                            lazyload(
                                RelationsFoundDB.matches.and_(MatchDB.rank < top_k)
                            )
                        )
                        .order_by(MatchDB.score.desc())
                        .execution_options(populate_existing=True)
                    )
                    col_matches = session.execute(stmt).all()
                    if len(col_matches) > 0:
                        for other_match in col_matches:
                            outlinks.targets.append(
                                OutLink(
                                    target=RelationsFound.from_db(other_match[0]),
                                    count=positive_others.shape[0],
                                    instances=positive_others.index.to_list(),
                                )
                            )
            return outlinks
