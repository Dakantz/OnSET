/* eslint-disable */
/* tslint:disable */
// @ts-nocheck
/*
 * ---------------------------------------------------------------
 * ## THIS FILE WAS GENERATED VIA SWAGGER-TYPESCRIPT-API        ##
 * ##                                                           ##
 * ## AUTHOR: acacode                                           ##
 * ## SOURCE: https://github.com/acacode/swagger-typescript-api ##
 * ---------------------------------------------------------------
 */

/** ResultAttributionType */
export enum ResultAttributionType {
  Topic = "topic",
  Query = "query",
}

/** RETURN_TYPE */
export enum RETURN_TYPE {
  Subject = "subject",
  Link = "link",
  Both = "both",
}

/** RELATION_TYPE */
export enum RELATION_TYPE {
  Property = "property",
  Instance = "instance",
}

/** OperationType */
export enum OperationType {
  Add = "add",
  Remove = "remove",
}

/** ManifoldAlg */
export enum ManifoldAlg {
  TSNE = "TSNE",
  MDS = "MDS",
  Smacof = "smacof",
}

/** FUZZY_QUERY_ORDER */
export enum FUZZY_QUERY_ORDER {
  Score = "score",
  Instances = "instances",
}

/** AssistantSubQueryType */
export enum AssistantSubQueryType {
  String = "string",
  Number = "number",
  Boolean = "boolean",
  Date = "date",
  Subject = "subject",
  QueryProp = "query_prop",
}

/** AssistantLink */
export interface AssistantLink {
  /**
   * Type
   * @default "link"
   */
  type?: "link";
  /** From Id */
  from_id: string;
  /** To Id */
  to_id: string;
  /** From Internal Id */
  from_internal_id: string;
  /** To Internal Id */
  to_internal_id: string;
  /** Link Id */
  link_id: string;
}

/** AssistantSubQuery */
export interface AssistantSubQuery {
  /**
   * Type
   * @default "subquery"
   */
  type?: "subquery";
  constraint_type: AssistantSubQueryType;
  /** Field */
  field: string;
  /** From Internal Id */
  from_internal_id: string;
  /** From Id */
  from_id: string;
}

/** AssistantSubject */
export interface AssistantSubject {
  /**
   * Type
   * @default "subject"
   */
  type?: "subject";
  /** Subject Id */
  subject_id: string;
  /** Internal Id */
  internal_id: string;
  /**
   * Subqueries
   * @default []
   */
  subqueries?: AssistantSubQuery[];
  /**
   * X
   * @default 0
   */
  x?: number;
  /**
   * Y
   * @default 0
   */
  y?: number;
}

/** Body_load_ontology_management_ontology_post */
export interface BodyLoadOntologyManagementOntologyPost {
  /** Ontology */
  ontology: string;
}

/** CandidateEntity */
export interface CandidateEntity {
  /** Identifier */
  identifier: string;
  /** Type */
  type: string;
  /**
   * Constraints
   * @default []
   */
  constraints?: Constraint[];
  /** Score */
  score: number;
  subject?: Subject | null;
}

/** CandidateRelation */
export interface CandidateRelation {
  /** Entity */
  entity: string;
  /** Relation */
  relation: string;
  /** Target */
  target: string;
  /** Score */
  score: number;
  link?: SubjectLink | null;
}

/** Candidates */
export interface Candidates {
  /**
   * Relations
   * @default []
   */
  relations?: CandidateRelation[];
  /**
   * Entities
   * @default []
   */
  entities?: CandidateEntity[];
  /**
   * Message
   * @default "Found Relations and Entities"
   */
  message?: string;
}

/** ClosestRequest */
export interface ClosestRequest {
  /** Embedding */
  embedding: number[] | null;
  /** Query */
  query: string | null;
  /** All Embeddings */
  all_embeddings: number[][];
  /**
   * N Closest
   * @default 5
   */
  n_closest?: number;
}

/** ClosestResponse */
export interface ClosestResponse {
  /** Index */
  index: number;
  /** Distance */
  distance: number;
}

/** Constraint */
export interface Constraint {
  /** Property */
  property: string;
  /** Value */
  value: string | null;
  /** Modifier */
  modifier: string | null;
}

/** DataTensorResp */
export interface DataTensorResp {
  /** Data */
  data: number[];
  /** Type */
  type: "float32" | "float64" | "int32" | "int64";
  /** Shape */
  shape: number[];
}

/** EnrichedEntitiesRelations */
export interface EnrichedEntitiesRelations {
  /**
   * Relations
   * @default []
   */
  relations?: EnrichedRelation[];
  /**
   * Entities
   * @default []
   */
  entities?: EnrichedEntity[];
  /**
   * Message
   * @default "Found Relations and Entities"
   */
  message?: string;
}

/** EnrichedEntity */
export interface EnrichedEntity {
  /** Identifier */
  identifier: string;
  /** Type */
  type: string;
  /**
   * Constraints
   * @default []
   */
  constraints?: Constraint[];
  subject: Subject;
}

/** EnrichedRelation */
export interface EnrichedRelation {
  /** Entity */
  entity: string;
  /** Relation */
  relation: string;
  /** Target */
  target: string;
  link: SubjectLink | null;
}

/** EntitiesRelations */
export interface EntitiesRelations {
  /**
   * Relations
   * @default []
   */
  relations?: Relation[];
  /**
   * Entities
   * @default []
   */
  entities?: Entity[];
  /**
   * Message
   * @default "Found Relations and Entities"
   */
  message?: string;
}

/** Entity */
export interface Entity {
  /** Identifier */
  identifier: string;
  /** Type */
  type: string;
  /**
   * Constraints
   * @default []
   */
  constraints?: Constraint[];
}

/** FuzzyQuery */
export interface FuzzyQuery {
  /** Q */
  q?: string | null;
  /** Topic Ids */
  topic_ids?: number[] | null;
  /**
   * Mix Topic Factor
   * @default 0.5
   */
  mix_topic_factor?: number | null;
  /** From Id */
  from_id?: string | string[] | null;
  /** To Id */
  to_id?: string | null;
  /**
   * Limit
   * @default 25
   */
  limit?: number | null;
  /**
   * Skip
   * @default 0
   */
  skip?: number | null;
  /** @default "both" */
  type?: RETURN_TYPE;
  /** @default "instance" */
  relation_type?: RELATION_TYPE | null;
  /** @default "score" */
  order?: FUZZY_QUERY_ORDER;
  /**
   * Include Thing
   * @default true
   */
  include_thing?: boolean;
  /**
   * Entity Type
   * @default "class"
   */
  entity_type?: string | null;
}

/** FuzzyQueryResult */
export interface FuzzyQueryResult {
  link?: SubjectLink | null;
  subject?: Subject | null;
  /**
   * Score
   * @default 0
   */
  score?: number;
  /**
   * Attributions
   * @default []
   */
  attributions?: ResultAttribution[];
}

/** FuzzyQueryResults */
export interface FuzzyQueryResults {
  /** Results */
  results: FuzzyQueryResult[];
}

/** GeneralizationQuery */
export interface GeneralizationQuery {
  /**
   * Cls
   * @default ""
   */
  cls?: string;
  /**
   * Out Link Ids
   * @default []
   */
  out_link_ids?: string[];
  /**
   * In Link Ids
   * @default []
   */
  in_link_ids?: string[];
}

/** HTTPValidationError */
export interface HTTPValidationError {
  /** Detail */
  detail?: ValidationError[];
}

/** Instance */
export interface Instance {
  /**
   * Id
   * @default ""
   */
  id?: string;
  /**
   * Label
   * @default ""
   */
  label?: string;
}

/** ManifoldRequest */
export interface ManifoldRequest {
  /** Embeddings */
  embeddings: number[][];
  /**
   * N Out
   * @default 2
   */
  n_out?: number;
  /** @default "TSNE" */
  alg?: ManifoldAlg;
  /**
   * Metric
   * @default "cosine"
   */
  metric?: string;
}

/** Match */
export interface Match {
  /**
   * Colname
   * @default ""
   */
  colname?: string;
  /**
   * Idx
   * @default ""
   */
  idx?: string;
  /**
   * Score
   * @default -1
   */
  score?: number;
  /**
   * Rank
   * @default -1
   */
  rank?: number;
}

/** Operation */
export interface Operation {
  operation: OperationType;
  /** Data */
  data: AssistantLink | AssistantSubject | AssistantSubQuery;
}

/** Operations */
export interface Operations {
  /**
   * Operations
   * @default []
   */
  operations?: Operation[];
}

/** OutLink */
export interface OutLink {
  target?: RelationsFound;
  /**
   * Count
   * @default 0
   */
  count?: number;
  /** Instances */
  instances?: string[];
}

/** Property */
export interface Property {
  /**
   * Property
   * @default ""
   */
  property?: string | null;
  /**
   * Label
   * @default ""
   */
  label?: string | null;
  /**
   * Values
   * @default []
   */
  values?: PropertyValue[];
}

/** PropertyValue */
export interface PropertyValue {
  /** Value */
  value: null;
  /** Label */
  label: string | null;
}

/** QueryGraph */
export interface QueryGraph {
  /**
   * Subjects
   * @default []
   */
  subjects?: AssistantSubject[];
  /**
   * Links
   * @default []
   */
  links?: AssistantLink[];
}

/** QueryProgress */
export interface QueryProgress {
  /** Id */
  id: string;
  /** Start Time */
  start_time: string;
  /**
   * Progress
   * @default 0
   */
  progress?: number;
  /** Max Steps */
  max_steps: number;
  /**
   * Message
   * @default ""
   */
  message?: string;
  /**
   * Relations Steps
   * @default []
   */
  relations_steps?: (
    | EntitiesRelations
    | Candidates
    | EnrichedEntitiesRelations
  )[];
  enriched_relations?: EnrichedEntitiesRelations | null;
}

/** Relation */
export interface Relation {
  /** Entity */
  entity: string;
  /** Relation */
  relation: string;
  /** Target */
  target: string;
}

/** RelationsFound */
export interface RelationsFound {
  /**
   * Id
   * @default 0
   */
  id?: number;
  /** Path */
  path?: string[];
  /**
   * Subject Id
   * @default ""
   */
  subject_id?: string;
  /**
   * Text
   * @default ""
   */
  text?: string;
  /** Matches */
  matches?: Match[];
}

/** ResultAttribution */
export interface ResultAttribution {
  /** Topic Id */
  topic_id?: number | null;
  /** @default "topic" */
  type?: ResultAttributionType;
  /**
   * Score
   * @default 0
   */
  score?: number;
}

/** SparqlQuery */
export interface SparqlQuery {
  /** Query */
  query: string;
  /**
   * Limit
   * @default 25
   */
  limit?: number | null;
  /**
   * Skip
   * @default 0
   */
  skip?: number | null;
}

/** SparseOutLinks */
export interface SparseOutLinks {
  source?: RelationsFound;
  /** Targets */
  targets?: OutLink[];
}

/** Subject */
export interface Subject {
  /** Subject Id */
  subject_id: string;
  /** Label */
  label: string;
  /**
   * Spos
   * @default {}
   */
  spos?: Record<string, Property>;
  /**
   * Subject Type
   * @default "class"
   */
  subject_type?: string;
  /**
   * Refcount
   * @default 0
   */
  refcount?: number;
  /**
   * Descendants
   * @default {}
   */
  descendants?: Record<string, Subject[]>;
  /**
   * Total Descendants
   * @default 0
   */
  total_descendants?: number;
  /**
   * Properties
   * @default {}
   */
  properties?: Record<string, Subject[]>;
  /**
   * Instance Count
   * @default 0
   */
  instance_count?: number;
}

/** SubjectLink */
export interface SubjectLink {
  /** Link Id */
  link_id: number;
  /** Label */
  label: string | null;
  /** From Id */
  from_id: string | null;
  /** Link Type */
  link_type: string;
  /** To Id */
  to_id: string | null;
  /** To Proptype */
  to_proptype: string | null;
  /** Property Id */
  property_id: string | null;
  from_subject: Subject | null;
  to_subject: Subject | null;
  /**
   * Instance Count
   * @default 0
   */
  instance_count?: number;
}

/** Topic */
export interface Topic {
  /** Topic Id */
  topic_id: number;
  /** Sub Topics */
  sub_topics: Topic[];
  /** Parent Topic Id */
  parent_topic_id: number | null;
  /** Topic */
  topic: string;
  /** Count */
  count: number;
  /** Subjects Ids */
  subjects_ids: string[];
  /** Property Ids */
  property_ids: string[];
}

/** ValidationError */
export interface ValidationError {
  /** Location */
  loc: (string | number)[];
  /** Message */
  msg: string;
  /** Error Type */
  type: string;
  /** Input */
  input?: any;
  /** Context */
  ctx?: object;
}

import type {
  AxiosInstance,
  AxiosRequestConfig,
  AxiosResponse,
  HeadersDefaults,
  ResponseType,
} from "axios";
import axios from "axios";

export type QueryParamsType = Record<string | number, any>;

export interface FullRequestParams
  extends Omit<AxiosRequestConfig, "data" | "params" | "url" | "responseType"> {
  /** set parameter to `true` for call `securityWorker` for this request */
  secure?: boolean;
  /** request path */
  path: string;
  /** content type of request body */
  type?: ContentType;
  /** query params */
  query?: QueryParamsType;
  /** format of response (i.e. response.json() -> format: "json") */
  format?: ResponseType;
  /** request body */
  body?: unknown;
}

export type RequestParams = Omit<
  FullRequestParams,
  "body" | "method" | "query" | "path"
>;

export interface ApiConfig<SecurityDataType = unknown>
  extends Omit<AxiosRequestConfig, "data" | "cancelToken"> {
  securityWorker?: (
    securityData: SecurityDataType | null,
  ) => Promise<AxiosRequestConfig | void> | AxiosRequestConfig | void;
  secure?: boolean;
  format?: ResponseType;
}

export enum ContentType {
  Json = "application/json",
  JsonApi = "application/vnd.api+json",
  FormData = "multipart/form-data",
  UrlEncoded = "application/x-www-form-urlencoded",
  Text = "text/plain",
}

export class HttpClient<SecurityDataType = unknown> {
  public instance: AxiosInstance;
  private securityData: SecurityDataType | null = null;
  private securityWorker?: ApiConfig<SecurityDataType>["securityWorker"];
  private secure?: boolean;
  private format?: ResponseType;

  constructor({
    securityWorker,
    secure,
    format,
    ...axiosConfig
  }: ApiConfig<SecurityDataType> = {}) {
    this.instance = axios.create({
      ...axiosConfig,
      baseURL: axiosConfig.baseURL || "",
    });
    this.secure = secure;
    this.format = format;
    this.securityWorker = securityWorker;
  }

  public setSecurityData = (data: SecurityDataType | null) => {
    this.securityData = data;
  };

  protected mergeRequestParams(
    params1: AxiosRequestConfig,
    params2?: AxiosRequestConfig,
  ): AxiosRequestConfig {
    const method = params1.method || (params2 && params2.method);

    return {
      ...this.instance.defaults,
      ...params1,
      ...(params2 || {}),
      headers: {
        ...((method &&
          this.instance.defaults.headers[
            method.toLowerCase() as keyof HeadersDefaults
          ]) ||
          {}),
        ...(params1.headers || {}),
        ...((params2 && params2.headers) || {}),
      },
    };
  }

  protected stringifyFormItem(formItem: unknown) {
    if (typeof formItem === "object" && formItem !== null) {
      return JSON.stringify(formItem);
    } else {
      return `${formItem}`;
    }
  }

  protected createFormData(input: Record<string, unknown>): FormData {
    if (input instanceof FormData) {
      return input;
    }
    return Object.keys(input || {}).reduce((formData, key) => {
      const property = input[key];
      const propertyContent: any[] =
        property instanceof Array ? property : [property];

      for (const formItem of propertyContent) {
        const isFileType = formItem instanceof Blob || formItem instanceof File;
        formData.append(
          key,
          isFileType ? formItem : this.stringifyFormItem(formItem),
        );
      }

      return formData;
    }, new FormData());
  }

  public request = async <T = any, _E = any>({
    secure,
    path,
    type,
    query,
    format,
    body,
    ...params
  }: FullRequestParams): Promise<AxiosResponse<T>> => {
    const secureParams =
      ((typeof secure === "boolean" ? secure : this.secure) &&
        this.securityWorker &&
        (await this.securityWorker(this.securityData))) ||
      {};
    const requestParams = this.mergeRequestParams(params, secureParams);
    const responseFormat = format || this.format || undefined;

    if (
      type === ContentType.FormData &&
      body &&
      body !== null &&
      typeof body === "object"
    ) {
      body = this.createFormData(body as Record<string, unknown>);
    }

    if (
      type === ContentType.Text &&
      body &&
      body !== null &&
      typeof body !== "string"
    ) {
      body = JSON.stringify(body);
    }

    return this.instance.request({
      ...requestParams,
      headers: {
        ...(requestParams.headers || {}),
        ...(type ? { "Content-Type": type } : {}),
      },
      params: query,
      responseType: responseFormat,
      data: body,
      url: path,
    });
  };
}

/**
 * @title Ontology Provenance API
 * @version 0.1.0
 */
export class Api<
  SecurityDataType extends unknown,
> extends HttpClient<SecurityDataType> {
  /**
   * No description
   *
   * @name ReadRootGet
   * @summary Read Root
   * @request GET:/
   */
  readRootGet = (params: RequestParams = {}) =>
    this.request<any, any>({
      path: `/`,
      method: "GET",
      format: "json",
      ...params,
    });

  sparql = {
    /**
     * No description
     *
     * @name SparqlQuerySparqlPost
     * @summary Sparql Query
     * @request POST:/sparql
     */
    sparqlQuerySparqlPost: (data: SparqlQuery, params: RequestParams = {}) =>
      this.request<Record<string, any>[], HTTPValidationError>({
        path: `/sparql`,
        method: "POST",
        body: data,
        type: ContentType.Json,
        format: "json",
        ...params,
      }),

    /**
     * No description
     *
     * @name SparqlQueryGetSparqlGet
     * @summary Sparql Query Get
     * @request GET:/sparql
     */
    sparqlQueryGetSparqlGet: (
      query: {
        /** Query */
        query: string;
      },
      params: RequestParams = {},
    ) =>
      this.request<Record<string, any>, HTTPValidationError>({
        path: `/sparql`,
        method: "GET",
        query: query,
        format: "json",
        ...params,
      }),
  };
  management = {
    /**
     * No description
     *
     * @name LoadOntologyManagementOntologyPost
     * @summary Load Ontology
     * @request POST:/management/ontology
     */
    loadOntologyManagementOntologyPost: (
      data: BodyLoadOntologyManagementOntologyPost,
      params: RequestParams = {},
    ) =>
      this.request<any, HTTPValidationError>({
        path: `/management/ontology`,
        method: "POST",
        body: data,
        type: ContentType.FormData,
        format: "json",
        ...params,
      }),
  };
  topics = {
    /**
     * No description
     *
     * @name GetTopicsRootTopicsRootGet
     * @summary Get Topics Root
     * @request GET:/topics/root
     */
    getTopicsRootTopicsRootGet: (
      query?: {
        /**
         * Force Initialize
         * @default false
         */
        force_initialize?: boolean;
      },
      params: RequestParams = {},
    ) =>
      this.request<Topic, HTTPValidationError>({
        path: `/topics/root`,
        method: "GET",
        query: query,
        format: "json",
        ...params,
      }),
  };
  classes = {
    /**
     * No description
     *
     * @name GetLlmResultsClassesSearchLlmGet
     * @summary Get Llm Results
     * @request GET:/classes/search/llm
     */
    getLlmResultsClassesSearchLlmGet: (
      query?: {
        /**
         * Q
         * @default "working field of person"
         */
        q?: string;
      },
      params: RequestParams = {},
    ) =>
      this.request<QueryProgress, HTTPValidationError>({
        path: `/classes/search/llm`,
        method: "GET",
        query: query,
        format: "json",
        ...params,
      }),

    /**
     * No description
     *
     * @name GetLlmResultsRunningClassesSearchLlmRunningGet
     * @summary Get Llm Results Running
     * @request GET:/classes/search/llm/running
     */
    getLlmResultsRunningClassesSearchLlmRunningGet: (
      query: {
        /** Query Id */
        query_id: string;
      },
      params: RequestParams = {},
    ) =>
      this.request<QueryProgress | null, HTTPValidationError>({
        path: `/classes/search/llm/running`,
        method: "GET",
        query: query,
        format: "json",
        ...params,
      }),

    /**
     * No description
     *
     * @name GetLlmExamplesClassesSearchLlmExamplesGet
     * @summary Get Llm Examples
     * @request GET:/classes/search/llm/examples
     */
    getLlmExamplesClassesSearchLlmExamplesGet: (params: RequestParams = {}) =>
      this.request<EnrichedEntitiesRelations[], any>({
        path: `/classes/search/llm/examples`,
        method: "GET",
        format: "json",
        ...params,
      }),

    /**
     * No description
     *
     * @name SearchClassesClassesSearchPost
     * @summary Search Classes
     * @request POST:/classes/search
     */
    searchClassesClassesSearchPost: (
      data: FuzzyQuery,
      params: RequestParams = {},
    ) =>
      this.request<FuzzyQueryResults, HTTPValidationError>({
        path: `/classes/search`,
        method: "POST",
        body: data,
        type: ContentType.Json,
        format: "json",
        ...params,
      }),

    /**
     * No description
     *
     * @name GetAssistantResultsClassesSearchAssistantPost
     * @summary Get Assistant Results
     * @request POST:/classes/search/assistant
     */
    getAssistantResultsClassesSearchAssistantPost: (
      data: QueryGraph,
      query?: {
        /**
         * Q
         * @default "working field of person"
         */
        q?: string;
      },
      params: RequestParams = {},
    ) =>
      this.request<Operations, HTTPValidationError>({
        path: `/classes/search/assistant`,
        method: "POST",
        query: query,
        body: data,
        type: ContentType.Json,
        format: "json",
        ...params,
      }),

    /**
     * No description
     *
     * @name EncodeTextClassesSearchEncodeTextPost
     * @summary Encode Text
     * @request POST:/classes/search/encode/text
     */
    encodeTextClassesSearchEncodeTextPost: (
      data: string,
      params: RequestParams = {},
    ) =>
      this.request<DataTensorResp, HTTPValidationError>({
        path: `/classes/search/encode/text`,
        method: "POST",
        body: data,
        type: ContentType.Json,
        format: "json",
        ...params,
      }),

    /**
     * No description
     *
     * @name EncodeImageClassesSearchEncodeImagePost
     * @summary Encode Image
     * @request POST:/classes/search/encode/image
     */
    encodeImageClassesSearchEncodeImagePost: (
      data: string,
      params: RequestParams = {},
    ) =>
      this.request<DataTensorResp, HTTPValidationError>({
        path: `/classes/search/encode/image`,
        method: "POST",
        body: data,
        type: ContentType.Json,
        format: "json",
        ...params,
      }),

    /**
     * No description
     *
     * @name GetNamedInstanceClassesInstancesGet
     * @summary Get Named Instance
     * @request GET:/classes/instances
     */
    getNamedInstanceClassesInstancesGet: (
      query: {
        /** Cls */
        cls: string;
      },
      params: RequestParams = {},
    ) =>
      this.request<Subject[], HTTPValidationError>({
        path: `/classes/instances`,
        method: "GET",
        query: query,
        format: "json",
        ...params,
      }),

    /**
     * No description
     *
     * @name GetNamedInstanceSearchClassesInstancesSearchGet
     * @summary Get Named Instance Search
     * @request GET:/classes/instances/search
     */
    getNamedInstanceSearchClassesInstancesSearchGet: (
      query: {
        /** Cls */
        cls: string;
        /** Q */
        q?: string | null;
        /**
         * Limit
         * @default 10
         */
        limit?: number;
        /**
         * Skip
         * @default 0
         */
        skip?: number;
      },
      params: RequestParams = {},
    ) =>
      this.request<Instance[], HTTPValidationError>({
        path: `/classes/instances/search`,
        method: "GET",
        query: query,
        format: "json",
        ...params,
      }),

    /**
     * No description
     *
     * @name GetNamedInstancePropertiesClassesInstancesPropertiesGet
     * @summary Get Named Instance Properties
     * @request GET:/classes/instances/properties
     */
    getNamedInstancePropertiesClassesInstancesPropertiesGet: (
      query: {
        /** Instance Id */
        instance_id: string;
      },
      params: RequestParams = {},
    ) =>
      this.request<Record<string, Property>, HTTPValidationError>({
        path: `/classes/instances/properties`,
        method: "GET",
        query: query,
        format: "json",
        ...params,
      }),

    /**
     * No description
     *
     * @name GetOutlinksClassesOutlinksGet
     * @summary Get Outlinks
     * @request GET:/classes/outlinks
     */
    getOutlinksClassesOutlinksGet: (
      query: {
        /** Subject Id */
        subject_id: string;
      },
      params: RequestParams = {},
    ) =>
      this.request<SparseOutLinks, HTTPValidationError>({
        path: `/classes/outlinks`,
        method: "GET",
        query: query,
        format: "json",
        ...params,
      }),

    /**
     * No description
     *
     * @name GetSubjectClassesSubjectsGet
     * @summary Get Subject
     * @request GET:/classes/subjects
     */
    getSubjectClassesSubjectsGet: (
      query: {
        /** Subject Id */
        subject_id: string;
      },
      params: RequestParams = {},
    ) =>
      this.request<Subject | null, HTTPValidationError>({
        path: `/classes/subjects`,
        method: "GET",
        query: query,
        format: "json",
        ...params,
      }),

    /**
     * No description
     *
     * @name GetLinkClassesLinksGet
     * @summary Get Link
     * @request GET:/classes/links
     */
    getLinkClassesLinksGet: (
      query: {
        /** Link Id */
        link_id: string;
      },
      params: RequestParams = {},
    ) =>
      this.request<SubjectLink | null, HTTPValidationError>({
        path: `/classes/links`,
        method: "GET",
        query: query,
        format: "json",
        ...params,
      }),

    /**
     * No description
     *
     * @name GetRelationsClassesRelationsGet
     * @summary Get Relations
     * @request GET:/classes/relations
     */
    getRelationsClassesRelationsGet: (
      query?: {
        /** Q */
        q?: string | null;
        /** From Id */
        from_id?: string | null;
        /** To Id */
        to_id?: string | null;
      },
      params: RequestParams = {},
    ) =>
      this.request<SubjectLink[], HTTPValidationError>({
        path: `/classes/relations`,
        method: "GET",
        query: query,
        format: "json",
        ...params,
      }),

    /**
     * No description
     *
     * @name GetFullClassesClassesFullGet
     * @summary Get Full Classes
     * @request GET:/classes/full
     */
    getFullClassesClassesFullGet: (params: RequestParams = {}) =>
      this.request<Subject[], any>({
        path: `/classes/full`,
        method: "GET",
        format: "json",
        ...params,
      }),

    /**
     * No description
     *
     * @name GetRootClassesClassesRootsGet
     * @summary Get Root Classes
     * @request GET:/classes/roots
     */
    getRootClassesClassesRootsGet: (params: RequestParams = {}) =>
      this.request<Subject[], any>({
        path: `/classes/roots`,
        method: "GET",
        format: "json",
        ...params,
      }),

    /**
     * No description
     *
     * @name GetClassClassesSubclassesGet
     * @summary Get Class
     * @request GET:/classes/subclasses
     */
    getClassClassesSubclassesGet: (
      query: {
        /** Cls */
        cls: string;
      },
      params: RequestParams = {},
    ) =>
      this.request<Subject[], HTTPValidationError>({
        path: `/classes/subclasses`,
        method: "GET",
        query: query,
        format: "json",
        ...params,
      }),

    /**
     * No description
     *
     * @name GetClassSearchClassesSubclassesSearchPost
     * @summary Get Class Search
     * @request POST:/classes/subclasses/search
     */
    getClassSearchClassesSubclassesSearchPost: (
      data: FuzzyQuery,
      params: RequestParams = {},
    ) =>
      this.request<FuzzyQueryResults, HTTPValidationError>({
        path: `/classes/subclasses/search`,
        method: "POST",
        body: data,
        type: ContentType.Json,
        format: "json",
        ...params,
      }),

    /**
     * No description
     *
     * @name GetMostGenericsClassesParentsMostGenericPost
     * @summary Get Most Generics
     * @request POST:/classes/parents/most_generic
     */
    getMostGenericsClassesParentsMostGenericPost: (
      data: GeneralizationQuery,
      params: RequestParams = {},
    ) =>
      this.request<Subject, HTTPValidationError>({
        path: `/classes/parents/most_generic`,
        method: "POST",
        body: data,
        type: ContentType.Json,
        format: "json",
        ...params,
      }),
  };
  nlp = {
    /**
     * No description
     *
     * @name NlpEmbeddingsNlpEmbeddingsGet
     * @summary Nlp Embeddings
     * @request GET:/nlp/embeddings
     */
    nlpEmbeddingsNlpEmbeddingsGet: (
      query: {
        /** Query */
        query: string;
      },
      params: RequestParams = {},
    ) =>
      this.request<Record<string, any>, HTTPValidationError>({
        path: `/nlp/embeddings`,
        method: "GET",
        query: query,
        format: "json",
        ...params,
      }),

    /**
     * No description
     *
     * @name NlpEmbeddingsClosestNlpEmbeddingsClosestPost
     * @summary Nlp Embeddings Closest
     * @request POST:/nlp/embeddings/closest
     */
    nlpEmbeddingsClosestNlpEmbeddingsClosestPost: (
      data: ClosestRequest,
      params: RequestParams = {},
    ) =>
      this.request<ClosestResponse[], HTTPValidationError>({
        path: `/nlp/embeddings/closest`,
        method: "POST",
        body: data,
        type: ContentType.Json,
        format: "json",
        ...params,
      }),

    /**
     * No description
     *
     * @name NlpEmbeddingsManifoldNlpEmbeddingsManifoldPost
     * @summary Nlp Embeddings Manifold
     * @request POST:/nlp/embeddings/manifold
     */
    nlpEmbeddingsManifoldNlpEmbeddingsManifoldPost: (
      data: ManifoldRequest,
      params: RequestParams = {},
    ) =>
      this.request<number[][], HTTPValidationError>({
        path: `/nlp/embeddings/manifold`,
        method: "POST",
        body: data,
        type: ContentType.Json,
        format: "json",
        ...params,
      }),
  };
}
