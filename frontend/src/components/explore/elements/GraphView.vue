<template>
    <g v-if="store" class="graph_view">
        <g v-for="link in store.links">
            <LinkComp :link="link" :store="store" :diff="diff" :mode="displayMode"
                @link-edit-clicked="emit('linkEditClicked', $event)" />
        </g>
        <g v-for="node in store.nodes" :key="node.internal_id">
            <NodeComp :subject="node" :store="store" :mode="displayMode" :diff="diff"
                @link-point-clicked="emit('linkPointClicked', $event)"
                @prop-point-clicked="emit('propPointClicked', $event)"
                @instance-search-clicked="emit('instanceSearchClicked', $event)"
                @type-point-clicked="emit('typePointClicked', $event)" :scale="viewportState.scale" />
        </g>
        <g v-if="diff">
            <g v-for="link in diff.diff_links.removed">
                <LinkComp :link="link.left" :store="store" :diff="diff" :mode="DisplayMode.SELECT" />
            </g>
            <g v-for="node in diff.diff_nodes.removed" :key="node.left.internal_id">
                <NodeComp :subject="node.left" :store="store" :mode="DisplayMode.SELECT" :diff="diff"
                    @link-point-clicked="emit('linkPointClicked', $event)"
                    @prop-point-clicked="emit('propPointClicked', $event)"
                    @instance-search-clicked="emit('instanceSearchClicked', $event)" :scale="viewportState.scale" />
            </g>
        </g>
    </g>
</template>
<script setup lang="ts">
import { onMounted, reactive, useTemplateRef, watch } from 'vue'
import { Link, SubjectNode } from '@/utils/sparql/representation';
import NodeComp from './Node.vue';
import LinkComp from './Link.vue';
import { RepositoryState, type NodeLinkRepository } from '@/utils/sparql/store';
import { DisplayMode, InstanceSelectorOpenEvent, SelectorOpenEvent } from '@/utils/sparql/helpers';
import type { PropertiesOpenEvent } from '@/utils/sparql/querymapper';
import type { NodeLinkRepositoryDiff } from '@/utils/sparql/diff';
import * as d3 from 'd3';
import { ViewPortState } from '@/utils/editing';



const emit = defineEmits<{
    linkPointClicked: [value: SelectorOpenEvent]
    linkEditClicked: [value: SelectorOpenEvent]
    typePointClicked: [value: SelectorOpenEvent]
    propPointClicked: [value: PropertiesOpenEvent]
    instanceSearchClicked: [value: InstanceSelectorOpenEvent],
    triggerInterface: [value: { trigger: () => void }]
}>()

const { store, diff, displayMode, simulate, rect, viewportState } = defineProps({
    store: {
        type: Object as () => NodeLinkRepository,
        required: true
    },
    displayMode: {
        type: String as () => DisplayMode,
        default: DisplayMode.SELECT
    },
    diff: {
        type: Object as () => NodeLinkRepositoryDiff | null,
        default: null
    },
    simulate: {
        type: Boolean,
        default: false
    },
    rect: {
        type: Object as () => { x: number, y: number, width: number, height: number },
        default: () => ({ x: 0, y: 0, width: 1000, height: 500 })
    },
    viewportState: {
        type: Object as () => ViewPortState,
        default: () => new ViewPortState(1, { x: 0, y: 0 })
    }
})

const state = reactive({
})
onMounted(() => {

    // console.log('bbox', svg_g_ref)
    // state.bbox = svg_g_ref.value.getBoundingClientRect()
    // start_simulation()
    emit('triggerInterface', {
        trigger: () => {
            start_simulation()
        }
    })
})


watch(() => simulate, (new_val) => {
    if (new_val) {
        start_simulation()
    }
}, { immediate: true })


const start_simulation = () => {
    if (!simulate) return
    if (!store) return
    console.log("Starting simulation for", store.nodes[0].subject_id, rect)
    store.state = RepositoryState.EDITING
    let mapped_links = store.links.map((link) => {
        return {
            ...link,
            source: link.from_internal_id,
            target: link.to_internal_id,
        }
    })
    const simulation = d3.forceSimulation(store.nodes)
        .force('charge', d3.forceManyBody().strength(2).distanceMax(500).distanceMin(50))
        .force('center', d3.forceCenter(rect.width / 2, rect.height / 2).strength(0.1))
        .force('link', d3.forceLink<SubjectNode, typeof mapped_links[0]>(mapped_links)
            .id((d) => d.internal_id)
            .strength(0.5)
        )
        .force('collide', d3.forceCollide<SubjectNode>(d => d.width / 2).strength(0.05))


    simulation.on('tick', () => {
        store.nodes.forEach((node) => {
            node.x = Math.max(0, Math.min(rect.width - node.width, node.x))
            node.y = Math.max(0, Math.min(rect.height - node.height, node.y))
        })
    })
    simulation.on('end', () => {
        store.state = RepositoryState.STABLE
        console.log("Simulation ended")
    })
    console.log("Started simulation for", store.nodes)
}
</script>
<style lang="css" scoped>
.graph_view {
    user-select: none;
}
</style>