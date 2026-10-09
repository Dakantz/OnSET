from pydantic import BaseModel, Field
from rdflib import Graph, URIRef, Literal
from model import (
    GeneralizationQuery,
    Instance,
    InstanceQuery,
    Property,
    PropertyValue,
    Subject,
    SubjectLink,
)
import pandas as pd
from rdflib.plugins.sparql import prepareQuery
from tqdm import tqdm
import traceback
from rdflib.plugins.parsers.notation3 import BadSyntax


class Prefix(BaseModel):
    ttl_prefix: str = Field(
        "bto", title="Prefix", description="Prefix to be used in the ontology"
    )
    uri: str = Field(
        "https://w3id.org/brainteaser/ontology/schema/",
        title="URI",
        description="URI to be used in the ontology",
    )


class OntologyConfig(BaseModel):
    ttl_prefixes: list[Prefix] = Field(
        [Prefix()],
        title="Prefixes",
        description="List of prefixes to be used in the ontology",
    )
    parent_class_query: str = Field(
        f"""SELECT ?cls
            WHERE {{
                    ?cls rdf:type owl:Class.
                    ?cls rdfs:label ?cls_lbl.
                    MINUS {{ ?cls rdfs:subClassOf ?sbcl}}.
            }}
                """,
        title="Parent Class Query",
        description="Query to get the parent classes",
    )
    sub_class_query: str = Field(
        f"""SELECT ?scls
                WHERE {{
                     ?scls rdf:type owl:Class.
                     ?scls rdfs:subClassOf ?cls.
                }}
                """,
        title="Sub Class Query",
        description="Query to get the sub classes",
    )
    property_types: list[str] = Field(
        [
            "owl:ObjectProperty",
            "owl:DatatypeProperty",
            "rdf:Property",
        ],
    )
    language: str = Field(
        "en", title="Language", description="Language of the ontology"
    )
    encoding_model: str = Field(
        "clip-ViT-B-32",
        title="Encoding Model",
        description="Model to be used for encoding",
    )
    ontology_extension: str = Field(
        """
        """
    )


INT_COMPATIBLE_TYPES = [
    "http://www.w3.org/2001/XMLSchema#int",
    "http://www.w3.org/2001/XMLSchema#integer",
    "http://www.w3.org/2001/XMLSchema#positiveInteger",
    "http://www.w3.org/2001/XMLSchema#nonNegativeInteger",
]
FLOAT_COMPATIBLE_TYPES = [
    "http://www.w3.org/2001/XMLSchema#float",
    "http://www.w3.org/2001/XMLSchema#double",
    "http://www.w3.org/2001/XMLSchema#decimal",
    # kilogram, seconds
]


class OntologyManager:
    def __init__(self, config: OntologyConfig, brainteaser_graph: Graph):
        self.config = config
        self.onto = brainteaser_graph
        self.addtional_graph: Graph | None = None
        if len(config.ontology_extension.strip()) > 0:
            try:
                self.addtional_graph = Graph()
                self.addtional_graph.parse(
                    data=config.ontology_extension, format="turtle"
                )
            except BadSyntax as bse:
                print(f"Error parsing ontology additions: {bse}")
                raise bse
        self.__label_cache: dict[str, str] = {}

    def __query(self, q: str):
        res = list(self.onto.query(q))
        if self.addtional_graph is not None:
            add_res = list(self.addtional_graph.query(q))
            res.extend(add_res)
        return res

    def __queries_res_raw(self, q: str):
        res = [self.onto.query(q)]
        if self.addtional_graph is not None:
            res.extend(self.addtional_graph.query(q))
        return res

    def q_to_df(self, q: str):
        results = list(self.__query(q))
        # for r in results:
        #     for t in r:
        #         if isinstance(t, URIRef):
        #             print(t.n3(onto.namespace_manager))
        #         else:
        #             print(t)
        # return pd.DataFrame(results).map(
        #     lambda x: x.n3(self.onto.namespace_manager) if hasattr(x, "n3") else x
        # )
        return pd.DataFrame(results)

    def q_to_df_values(self, q: str) -> pd.DataFrame:
        result_sets = self.__queries_res_raw(q)
        assert len(result_sets) > 0, "Expected non-empty result set"
        cols = [str(var) for var in result_sets[0].vars]
        results = [
            dict(zip(cols, row)) for result_set in result_sets for row in result_set
        ]
        results_df = pd.DataFrame(results)
        results_df = results_df.map(self.to_readable)
        return results_df

    def df_to_labels(self, df: pd.DataFrame):
        labeled_df = df.copy()
        for i, row in df.iterrows():
            for j, col in row.items():
                data = list(
                    self.__query(f"SELECT ?label WHERE {{ {col} rdfs:label ?label }}")
                )
                labeled_df.at[i, j] = data[0][0] if data else col
        return labeled_df

    def get_root_classes(self, load_properties=False) -> list[Subject]:
        classes = self.q_to_df(self.config.parent_class_query)
        if classes.empty:
            # if no parent classes, return all classes belonging to owl:Thing
            print(
                "No parent classes found, returning all classes belonging to owl:Thing"
            )
            classes = self.q_to_df(
                f"""
                SELECT ?cls
                WHERE {{
                    ?cls rdf:type owl:Class.
        			?cls rdfs:subClassOf owl:Thing.   
                }}
                """
            )
        classes_list = classes[0].tolist()
        onto_classes: list[Subject] = [
            self.enrich_subject(cls, load_properties=load_properties)
            for cls in tqdm(classes_list, desc="Loading root classes")
        ]
        return onto_classes

    def get_subclasses(self, cls: str, load_properties=False) -> list[Subject]:
        # query = prepareQuery(
        #     queryString=self.config.sub_class_query,
        #     initNs={
        #         prefix.ttl_prefix: prefix.uri for prefix in self.config.ttl_prefixes
        #     },
        # )
        classes = list(
            self.__query(
                self.config.sub_class_query.replace("?cls", cls),
            )
        )
        onto_classes: list[Subject] = [
            self.enrich_subject(cls[0], load_properties=load_properties)
            for cls in classes
        ]
        return onto_classes

    def get_all_subclasses(self, cls: str) -> list[Subject]:
        query = f"""SELECT ?scls
                    WHERE {{
                         ?scls rdf:type owl:Class.
                         ?scls rdfs:subClassOf* {cls}.
                    }}
                    """
        classes = list(
            self.__query(
                query,
            )
        )
        onto_classes: list[Subject] = [
            self.enrich_subject(cls[0], subject_type="class") for cls in classes
        ]
        return onto_classes

    def get_named_individuals(self, cls: str, limit=128) -> list[Subject]:
        query = f"""SELECT ?ind
                    WHERE {{
                         ?ind rdf:type owl:NamedIndividual.
                         ?ind rdf:type {cls}.
                    }}
                    LIMIT {limit}
                    """
        individuals = list(
            self.__query(
                query,
                # initBindings={"cls": cls},
            )
        )
        onto_classes: list[Subject] = [
            self.enrich_subject(ind[0], subject_type="individual")
            for ind in individuals
        ]

        return onto_classes

    def get_instances(self, query: InstanceQuery) -> list[Instance]:
        if query.q is None:
            query.q = ""
        individuals = self.q_to_df_values(
            f"""SELECT DISTINCT ?ind ?ind_lbl
                    WHERE {{
                        ?ind rdf:type {query.cls}.
                        ?ind rdfs:label ?ind_lbl.
                        FILTER (lang(?ind_lbl) = "{self.config.language}")
                        FILTER (CONTAINS(LCASE(?ind_lbl), LCASE("{query.q}")))
                    }}
                    ORDER BY ?ind ?ind_lbl
                    LIMIT {query.limit} OFFSET {query.skip} 
                    """
        )
        return [
            Instance(id=ind["ind"], label=ind["ind_lbl"])
            for i, ind in individuals.iterrows()
        ]

    def label_for(self, subject: str):
        if subject in self.__label_cache:
            return self.__label_cache[subject]
        labels = self.outgoing_edges_for(subject, ["rdfs:label"])
        if len(labels) == 0:
            label = subject
        else:
            label = labels["rdfs:label"].first_value()
        if label is None:
            label = subject
        if isinstance(label, Literal):
            label = label.value
        self.__label_cache[subject] = label
        return label

    def to_readable(self, cls: str | Literal | URIRef):
        if isinstance(cls, Literal):
            value = cls.title()
            if cls.datatype is not None:
                try:
                    cls_dtype = str(cls.datatype)
                    if cls_dtype in INT_COMPATIBLE_TYPES:
                        value = int(value)
                    elif (
                        cls_dtype in FLOAT_COMPATIBLE_TYPES
                        or "kilogram" in cls.datatype
                        or "metre" in cls.datatype
                        or "seconds" in cls.datatype
                        or "minute" in cls.datatype
                        or "hour" in cls.datatype
                        or "day" in cls.datatype
                    ):
                        value = float(value)
                except Exception as e:
                    print(traceback.format_exc())
                    print("Failed to convert", value, "to int or float", e)
            return value

        elif isinstance(cls, URIRef) or hasattr(cls, "n3"):
            return cls.n3(self.onto.namespace_manager)
        else:
            return cls

    def to_readable_literals(self, cls: str | Literal | URIRef):
        if isinstance(cls, Literal):
            return cls.value
        else:
            return cls

    def __label_candidates(self, data: list[tuple[URIRef, Literal]]):
        label_candidates: dict[str, list[str]] = {}
        for ref, label in data:
            if isinstance(ref, Literal):
                if (
                    hasattr(ref, "language") and ref.language == self.config.language
                ) or ref.language is None:
                    ref_n3 = ref.value
                else:
                    continue
            else:
                ref_n3 = self.to_readable(ref)
            if ref_n3 not in label_candidates:
                label_candidates[ref_n3] = []
            if isinstance(label, Literal) and hasattr(label, "language"):
                if label.language == self.config.language or label.language is None:
                    label_candidates[ref_n3].append(label.value)
        return label_candidates

    def outgoing_edges_for(self, cls: str, edges: list[str] = [], limit=128):
        if cls.startswith("_"):
            print("Skipping", cls)
            return {}
        try:
            # print("Loading outgoing edges for", cls, edges)
            if edges and len(edges) > 0:
                outgoing_edges = list(
                    self.__query(
                        f"""
                    SELECT DISTINCT ?edge ?edge_lbl ?obj ?obj_lbl WHERE {{ {cls} ?edge ?obj. FILTER (?edge in ({", ".join(edges)})) 
OPTIONAL {{?edge rdfs:label ?edge_label.}}
OPTIONAL {{?obj rdfs:label ?obj_lbl.}}
                    }}
                    LIMIT {limit}
                    """
                    )
                )
            else:
                outgoing_edges = list(
                    self.__query(
                        f"""
                    SELECT DISTINCT ?edge ?edge_lbl ?obj ?obj_lbl WHERE {{ {cls} ?edge ?obj. 
OPTIONAL {{?edge rdfs:label ?edge_label.}}
OPTIONAL {{?obj rdfs:label ?obj_lbl.}}
                    }}
                    LIMIT {limit}"""
                    )
                )
            outgoing_edge_label_candidates: dict[str, list[str]] = (
                self.__label_candidates(
                    [(edge, edge_lbl) for edge, edge_lbl, _, _ in outgoing_edges]
                )
            )

            outgoing_edges_dict: dict[str, Property] = {}
            for edge_n3 in outgoing_edge_label_candidates:
                values_candidates = self.__label_candidates(
                    [
                        (obj, obj_lbl)
                        for edge, _, obj, obj_lbl in outgoing_edges
                        if self.to_readable(edge) == edge_n3
                    ]
                )
                values = [
                    PropertyValue(
                        value=obj,
                        label=(
                            values_candidates[obj][0]
                            if len(values_candidates[obj]) > 0
                            else None
                        ),
                    )
                    for obj in values_candidates
                ]
                label = (
                    outgoing_edge_label_candidates[edge_n3][0]
                    if len(outgoing_edge_label_candidates[edge_n3]) > 0
                    else None
                )
                edge = Property(
                    property=edge_n3,
                    label=label,
                    values=values,
                )
                outgoing_edges_dict[edge_n3] = edge
            return outgoing_edges_dict
        except Exception as e:
            print(traceback.format_exc(), e, cls)
            return {}

    def refcount(self, cls):
        try:
            refcount = list(
                self.__query(
                    f"""
                SELECT (COUNT(?s) as ?count) WHERE {{ ?s ?p {cls}. }}"""
                )
            )
            return refcount[0][0].value
        except Exception as e:
            print(traceback.format_exc())
            return 0

    def properties_for(
        self, cls: str, property_type: str = "ObjectProperty", n_props=None
    ) -> list[Subject]:
        if cls.startswith("_"):
            print("Skipping", cls)
            return []
        try:
            # print("Loading properties for", cls)
            properties = list(
                self.__query(
                    f"""
                SELECT DISTINCT ?prop WHERE {{ 
                ?prop rdf:type {property_type}.
                {{?prop rdfs:domain/(owl:unionOf/rdf:rest*/rdf:first)* {cls}. }}
                UNION
                {{?prop rdfs:domain {cls}. }}
                }} {f"LIMIT {n_props}" if n_props else ""}"""
                )
            )
            # print("Loaded", len(properties), "properties for", cls)
            props_mapped: list[Subject] = [
                self.enrich_subject(prop[0], subject_type="individual")
                for prop in properties
            ]
            return props_mapped
        except Exception as e:
            print(traceback.format_exc())
            print("Failed to load properties for", cls)
            return []

    def range_of(self, prop: str, n_ranges: int = None):
        try:
            # print("Loading properties for", cls)
            ranges = list(
                self.__query(
                    f"""
                SELECT DISTINCT ?range WHERE {{ 
                {prop} rdfs:range/(owl:unionOf/rdf:rest*/rdf:first)* ?range.
                }} {f"LIMIT {n_ranges}" if n_ranges else ""}"""
                )
            )
            # print("Loaded", len(properties), "properties for", cls)
            ranges_mapped: list[Subject] = [
                self.enrich_subject(r[0], subject_type="individual") for r in ranges
            ]
            return ranges_mapped
        except Exception as e:
            print(traceback.format_exc())
            print("Failed to load range of", prop, e)
            return []

    def open_properties(self):
        open_properties = list(
            self.__query(
                """SELECT DISTINCT ?prop WHERE {
                    ?prop rdf:type rdf:Property .
                    ?prop rdfs:range/(owl:unionOf/rdf:rest*/rdf:first)* ?range.
                    MINUS {
                        ?prop rdfs:domain ?o .
                    }
                }"""
            )
        )
        return [prop[0].n3(self.onto.namespace_manager) for prop in open_properties]

    def enrich_subject(
        self, cls: str | None, subject_type="class", load_properties=False
    ):
        if cls is None:
            return None
        col_ref = cls.n3(self.onto.namespace_manager) if hasattr(cls, "n3") else cls

        # print("Enriching", col_ref)
        outgoing_edges = self.outgoing_edges_for(
            col_ref,
            edges=[
                "rdfs:label",
                "rdfs:range",
                "rdfs:domain",
                "rdfs:subPropertyOf",
                "rdfs:subClassOf",
                "rdf:type",
            ],
        )
        label_prop: Property = outgoing_edges.get(
            "rdfs:label",
            Property(values=[PropertyValue(value=col_ref, label=None)]),
        )
        subject = Subject(
            subject_id=col_ref,
            label=label_prop.first_value(),
            spos=outgoing_edges,
            subject_type=subject_type,
            instance_count=self.instance_count(col_ref),
            # refcount=refs,
        )
        if load_properties:
            subject.properties = {
                prop_type: self.properties_for(
                    col_ref, property_type=prop_type, n_props=512
                )
                for prop_type in self.config.property_types
            }
        return subject
        # refs = self.refcount(col_ref)

    def load_full_graph(self, depth=10) -> list[Subject]:
        roots = self.get_root_classes(load_properties=True)

        def enrich_descendants(cls: Subject, d=depth):
            # print("enriching", cls.subject_id)
            cls.total_descendants = 1  # self
            if d <= 0:
                return []
            try:
                subclasses = self.get_subclasses(cls.subject_id, load_properties=True)
                cls.descendants["subClass"] = [
                    enrich_descendants(subcls, d=d - 1) for subcls in subclasses
                ]
            except Exception as e:
                print(traceback.format_exc())
            try:
                named_ind = self.get_named_individuals(cls.subject_id)
                cls.descendants["namedIndividual"] = [
                    enrich_descendants(ni, d=d - 1) for ni in named_ind
                ]
            except Exception as e:
                print(traceback.format_exc())

            return cls

        roots = [
            enrich_descendants(cls)
            for cls in tqdm(roots, desc="Enriching root classes")
        ]
        self.roots_cache = roots
        return roots

    def get_full_classes(self) -> list[Subject]:
        if hasattr(self, "roots_cache"):
            return self.roots_cache
        graph = self.load_full_graph()
        return graph

    def instance_count(self, cls: str):
        return self.q_to_df(
            f"SELECT DISTINCT (COUNT(?s) as ?count) WHERE {{?s a {cls}}}"
        )[0][0].value

    def property_count(self, cls: str):
        return list(
            self.__query(f"SELECT DISTINCT (COUNT(?s) as ?count) WHERE {{?s {cls} ?o}}")
        )[0][0].value

    def get_parents(self, cls: str) -> list[str]:
        parents = self.q_to_df_values(
            f"""SELECT DISTINCT ?p WHERE {{ {cls} rdfs:subClassOf* ?p. }}"""
        )
        if "p" not in parents.columns:
            return []
        return parents["p"].to_list()

    def get_instance_properties(self, instance_id: str) -> list[dict[str, str]]:
        properties = self.q_to_df_values(
            f"SELECT DISTINCT ?p ?o WHERE {{ {instance_id} ?p ?o }}"
        )
        return properties.to_dict(orient="records")

    def get_most_generic_classes(self, q: GeneralizationQuery):
        """
        Determine the most generic parent classes for a given class.
        Strategy:
        * Get all parent classes of the given class
        * Find the classes linked by the in/out links
        * Choose the highest class with at least one in/out link
        """
        query = f"""SELECT ?cls (count(?mid) as ?distance)
                     WHERE {{
                        ?cls rdf:type owl:Class.
                        {q.cls} rdfs:subClassOf* ?mid .
                        ?mid rdfs:subClassOf+ ?cls .
                    }}
                    group by ?cls ?distance 
                    order by  DESC(?distance) 
                    """
        classes = list(
            self.__query(
                query,
            )
        )

        class LinkedSubject(Subject):
            out_links: list[SubjectLink] = Field([])
            in_links: list[SubjectLink] = Field([])

        parent_classes: list[LinkedSubject] = [
            self.enrich_subject(cls[0], subject_type="class") for cls in classes
        ] + [self.enrich_subject(q.cls, subject_type="class")]
        parent_classes = [
            LinkedSubject.model_validate(cls.model_dump()) for cls in parent_classes
        ]
        out_links = [
            self.enrich_subject(link, subject_type="link").to_link()
            for link in q.out_link_ids
        ]
        in_links = [
            self.enrich_subject(link, subject_type="link").to_link()
            for link in q.in_link_ids
        ]
        for parent_class in parent_classes:
            parent_class.out_links = [
                link for link in out_links if link.from_id == parent_class.subject_id
            ]
            parent_class.in_links = [
                link for link in in_links if link.to_id == parent_class.subject_id
            ]
        for parent_class in parent_classes:
            if len(parent_class.out_links) > 0:
                return parent_class
            if len(parent_class.in_links) > 0:
                return parent_class
        return parent_classes[0]
