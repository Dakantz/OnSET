import type { FuzzyQueryResult, QueryGraph, Subject } from "@/api/client.ts/Api";
import { jsonClone, registerClass } from "../parsing";
import { OpenEventType } from "./helpers";
import { Link, LinkType, QueryProp, QuerySet, SubjectConstraint, SubjectNode, SubQuery, type QuerySetGenerator } from "./representation";
import type { Diffable } from "./diff";
import { el } from "vuetify/locale";


@registerClass
export class MixedResponse<N extends Subject = Subject> implements FuzzyQueryResult {
    link: Link<N>;
    subject: SubjectNode;
    score: number;
    store: NodeLinkRepository;
    compute_layout: boolean = false;
    constructor(result: FuzzyQueryResult = null) {
        for (const key in result) {
            if (Object.prototype.hasOwnProperty.call(result, key)) {
                this[key] = result[key];
            }
        }
        this.store = new NodeLinkRepository()
        if (this.subject) {
            this.subject = new SubjectNode(result.subject)
            this.store.nodes.push(this.subject)
        }
        if (this.link) {
            this.link = new Link(result.link)
            let from_subject = new SubjectNode(result.link.from_subject)
            let to_subject = new SubjectNode(result.link.to_subject)
            this.link.from_internal_id = from_subject.internal_id
            this.link.to_internal_id = to_subject.internal_id
            this.store.links.push(this.link)
            this.store.nodes.push(...[from_subject, to_subject])

        }
    }

}
export enum RepositoryState {
    STABLE,
    EDITING,
}
@registerClass
export class NodeLinkRepository<N extends SubjectNode = SubjectNode, L extends Link = Link> implements Diffable, QuerySetGenerator {
    nodes: N[] = []
    links: L[] = []
    state: RepositoryState = RepositoryState.STABLE
    private static internal_id_cnt = 0
    _id: string | number
    constructor(nodes: N[] = [], links: L[] = []) {
        this.nodes = nodes
        this.links = links
        this._id = NodeLinkRepository.internal_id_cnt++
    }
    get id() {
        return this._id
    }
    changed(other: NodeLinkRepository): boolean {
        return this._id !== other._id
    }
    fromLinks(node: SubjectNode): L[] {
        return this.links.filter(link => link.from_internal_id === node.internal_id)
    }
    toLinks(node: SubjectNode): L[] {
        return this.links.filter(link => link.to_internal_id === node.internal_id)
    }
    from(link: Link): N | null {
        let outnodes = this.nodes.filter(node => node.internal_id === link.from_internal_id)
        return outnodes.length ? outnodes[0] : null
    }
    to(link: Link): N | null {
        let outnodes = this.nodes.filter(node => node.internal_id === link.to_internal_id)
        return outnodes.length ? outnodes[0] : null
    }
    node(n: N): N | null {
        let outnodes = this.nodes.filter(node => node.internal_id === n.internal_id)
        return outnodes.length ? outnodes[0] : null
    }
    link(l: Link): L | null {
        let outlinks = this.links.filter(link => link.id === l.id)
        return outlinks.length ? outlinks[0] : null
    }
    sameLinks(link: L): L[] {
        return this.links.filter(l => l.from_internal_id === link.from_internal_id && l.to_internal_id === link.to_internal_id)
    }
    circularLink(link: L): boolean {
        return link.from_internal_id === link.to_internal_id
    }
    addOutlink(link: L, origin: N, target: N, side: OpenEventType) {
        if (this.nodes.filter(node => node === origin).length === 0) {
            this.nodes.push(origin)
        }
        if (this.nodes.filter(node => node === target).length === 0) {
            this.nodes.push(target)
        }
        link = this.prepareLink(link, origin, target, side)
        this.links.push(link)
    }
    prepareLink(link: L, origin: N, target: N, side: OpenEventType) {
        switch (side) {
            case OpenEventType.FROM:
                link.from_internal_id = target.internal_id
                link.to_internal_id = origin.internal_id
                break
            case OpenEventType.TO:
                link.from_internal_id = origin.internal_id
                link.to_internal_id = target.internal_id
                break
            // default:
            //     throw new Error("Invalid side")
        }
        return link
    }
    removeLink(link: L) {
        if (link) {
            this.links = this.links.filter(l => l.link_id !== link.link_id)
        }
    }
    removeNode(node: N) {
        if (node) {
            this.nodes = this.nodes.filter(n => n.internal_id !== node.internal_id)
            this.links = this.links.filter(l => l.from_internal_id !== node.internal_id && l.to_internal_id !== node.internal_id)
        }
    }
    subElementsRecursive(node: SubjectNode, visited: SubjectNode[] = []) {
        let subNodes: SubjectNode[] = []
        let subLinks: Link[] = []
        let all_links = [...this.fromLinks(node), ...this.toLinks(node)]
        subLinks.push(...all_links)
        for (let link of all_links) {
            let to = this.to(link)
            let from = this.from(link)
            let target = from === node ? to : from
            if (!target || visited.includes(target) || node.internal_id_cnt > target.internal_id_cnt) {
                continue
            }
            visited.push(target)
            subNodes.push(target)
            subLinks.push(link)
            let subEdges = this.subElementsRecursive(target, visited)
            subNodes.push(...subEdges.nodes)
            subLinks.push(...subEdges.links)
        }
        return {
            nodes: subNodes,
            links: subLinks
        }
    }
    subElements(node: SubjectNode) {
        return this.subElementsRecursive(node)
    }

    deleteWithSubnodes(node: SubjectNode) {
        let subElements = this.subElements(node)
        console.log("Subelements", subElements)
        let subNodeIds = subElements.nodes.map(n => n.internal_id)
        this.nodes = this.nodes.filter(n => !subNodeIds.includes(n.internal_id))

        let subLinkIds = subElements.links.map(l => l.link_id)
        this.links = this.links.filter(l => !subLinkIds.includes(l.link_id))

        this.nodes = this.nodes.filter(n => n.internal_id != node.internal_id)
    }
    linksBetweenNodes(): Record<string, L[]> {
        let links = {}
        for (let link of this.links) {
            if (this.nodes.filter(node => node.internal_id === link.from_internal_id).length === 0 ||
                this.nodes.filter(node => node.internal_id === link.to_internal_id).length === 0) {
                continue
            }
            let from = this.from(link)
            let to = this.to(link)
            let link_hash = `${from.internal_id}-${to.internal_id}`

            if (!links.hasOwnProperty(link_hash)) {
                links[link_hash] = []
            }
            links[link_hash].push(link)
        }
        return links
    }


    textAttachPoint(link: L, circular: boolean = false): { x: number, y: number } {
        let from = this.from(link)
        let to = this.to(link)
        if (!from || !to) {
            console.warn("Link has no from or to node", link, from, to)
            return { x: 0, y: 0 }
        }
        //circular
        if (this.circularLink(link) || circular) {
            return { x: from.x + from.width / 2, y: from.y - from.height * 2 }
        } else {
            let from_pt = { x: from.x + from.width, y: from.y + from.height / 2 }
            let to_pt = { x: to.x, y: to.y + to.height / 2 }
            return {
                x: (from_pt.x + to_pt.x) / 2,
                y: (from_pt.y + to_pt.y) / 2
            }
        }

    }

    generateQuery(limit: number | null = 100, skip: number | null = null, distinct: boolean = true): string {
        let set = this.querySet()
        let output_names = Object.values(set.nodes).map(nd => nd.outputId())
        let query = `
        PREFIX tensorIndex: <https://qlever.cs.uni-freiburg.de/tensorIndex/>
        PREFIX dtf: <https://w3id.org/rdf-tensor/functions#>
        SELECT ${distinct ? "DISTINCT" : ""} ${output_names.join(" ")} ${set.output_ids.join(" ")} WHERE {`

        for (let link of set.link_triplets) {
            if (link.semantic_link_type === LinkType.STRUCTURAL) {
                query += `\n${link.from_id} ${link.link_id} ${link.to_id}.`
            } else if (link.semantic_link_type === LinkType.SIMILARITY) {
                query += `\n${link.from_id} ${link.link_id} ${link.from_id}_emb.
                 SERVICE tensorIndex: {
                    _:config tensorIndex:numNN 1 ;
                    tensorIndex:left ${link.from_id}_emb ;
                    tensorIndex:bindDistance ?dist ;
                    tensorIndex:payload ?s, ?thumb_ship_emb ;
                    tensorIndex:searchK 1 ;
                    tensorIndex:kIVF 512 ;
                    tensorIndex:experimentalRightCacheName "${link.from_id}-${link.to_id}" ;
                    tensorIndex:right ?${link.to_id}_emb ;
                    tensorIndex:algorithm tensorIndex:ivf ;
                    tensorIndex:distance tensorIndex:dot .
                    {
                        ${link.to_id} ${link.link_id} ${link.to_id}_emb ;
                    }
                }`
            }
        }

        for (let node of Object.values(set.nodes)) {
            if (set.nodes.hasOwnProperty(node.internal_id)) {
                // console.log(internal_id, set.internal_ids[internal_id])
                query += `\n${node.outputId()} a ${node.subject_id}.
    OPTIONAL {${node.outputId()} rdfs:label ${node.labelId()}.}`
                query += `\nOPTIONAL {${node.outputId()} foaf:name ${node.labelId()}.}`
            }
        }
        for (let constraint of set.filter) {
            let from = this.from(constraint.link)
            let constrained_id = constraint.propVar()
            let expression = constraint.expression(constrained_id)
            if (constraint instanceof SubjectConstraint) {
                if (constraint.instance) {
                    query += `\nFILTER(${from.outputId()}=${constraint.instance.id})`
                }
            } else if (constraint instanceof QueryProp || !expression || expression.length === 0) {
                query += `\n${from.outputId()} ${constraint.link.property_id} ${constrained_id}.`
            } else {
                query += `\n${from.outputId()} ${constraint.link.property_id} ${constrained_id}.
                ${constraint.expression(constrained_id)}`
            }
        }
        query += "\n}"
        const post_query_expressions = set.filter.map((constraint) => constraint.postQueryExpression(constraint.propVar())).filter(expr => expr.length > 0)
        if (post_query_expressions.length > 0) {
            query += "\n" + post_query_expressions.join("\n")
        } else {
            query += "\nORDER BY " + set.output_ids.join(" ")
        }
        if (limit) {
            query += `\nLIMIT ${limit}`
        }
        if (skip) {
            query += `\nOFFSET ${skip}`
        }
        return query
    }
    queryReadable(): string {
        let set = this.querySet()
        let text = ""
        for (let link of this.links) {
            let from = set.nodes[link.from_internal_id]
            let to = set.nodes[link.to_internal_id]
            text += `${from.label} ${link.label} ${to.label}\n`
        }
        for (let node of Object.values(set.nodes)) {
            text += `${node.id} a ${node.label}\n`
            for (let constraint of node.subqueries) {
                if (constraint instanceof SubjectConstraint) {
                    if (constraint.instance) {
                        text += `${node.label} is exactly ${constraint.instance.label}\n`
                    }
                } else if (constraint instanceof QueryProp) {
                    text += `${node.label}'s ${constraint.link.label} ${constraint.expression(constraint.propVar())}\n`
                }
            }
        }
        return text
    }
    querySet(): QuerySet {
        let set = new QuerySet()

        for (let node of this.nodes) {
            set.nodes[node.internal_id] = node
            set.filter.push(...node.subqueries)
        }

        set.output_ids = Object.values(set.nodes).map(nd => nd.labelId())
        set.output_ids.push(...set.filter.map((constraint) => constraint.link.outputId()))
        for (let link of this.links) {
            let from = this.from(link)
            let to = this.to(link)
            let link_id = link.queryId()
            if (link.allow_arbitrary) {
                set.output_ids.push(link_id)
            }
            set.link_triplets.push({
                from_id: from.outputId(),
                link_id: link_id,
                to_id: to.outputId(),
                semantic_link_type: link.semantic_link_type
            })
        }
        return set
    }
    toQueryGraph(): QueryGraph {
        let query_graph = {} as QueryGraph
        query_graph.subjects = this.nodes.map(node => {
            return {
                internal_id: node.internal_id,
                subject_id: node.subject_id,
                label: node.label,
                type: "subject",
                x: node.x,
                y: node.y,
                subqueries: []
            }
        })
        query_graph.links = this.links.map(link => {
            return {
                from_id: link.from_id,
                to_id: link.to_id,
                link_id: link.property_id,
                from_internal_id: link.from_internal_id,
                to_internal_id: link.to_internal_id,
                type: "link",
            }
        })
        return query_graph
    }

}