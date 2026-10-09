<template>
    <div class="query_builder" ref="svg_wrapper">
        <svg class="query_build_wrapper">
            <g>
                <rect class="capture_rect" :width="ui_state.rect.width" :height="ui_state.rect.height"
                    @wheel="scroll_box" @mousedown.capture="startDrag($event)" @mousemove.capture="drag($event)"
                    @mouseup.capture="endDrag($event)" @mouseleave.capture="endDrag($event)">
                </rect>
            </g>
            <g
                :transform="`scale(${ui_state.viewportState.scale}) translate(${ui_state.viewportState.offset.x}, ${ui_state.viewportState.offset.y})`">
                <GraphView :store="store" :display-mode="DisplayMode.EDIT" :diff="diff"
                    @link-point-clicked="clickedOutlink($event)" @instance-search-clicked="clickedInstance($event)"
                    @type-point-clicked="clickedType($event)" @link-edit-clicked="clickedEditLink($event)"
                    :simulate="ui_state.run_simulation" @trigger-interface="ui_state.trigger_sim = $event.trigger"
                    :rect="ui_state.rect" :viewport-state="ui_state.viewportState"></GraphView>
                <LinkComposer :store="store" :evt="ui_state.attaching_event" @selection-complete="linkEditDone($event)"
                    :viewport="ui_state.viewportState">
                </LinkComposer>
                <OutLinkSelector :selection_event="ui_state.sublink_event" v-model="ui_state.sublink_display"
                    :store="store" @hover_option="ui_state.hoveredLink = $event" @finished="linkSelectDone($event)">
                </OutLinkSelector>
                <InstanceSelector :selection_event="ui_state.instance_event" v-model="ui_state.instance_display">
                </InstanceSelector>
                <TypeSelector :selection_event="ui_state.type_event" v-model="ui_state.type_display" :store="store">
                </TypeSelector>
            </g>
            <use xlink:href="#outlink_selector"></use>
            <use xlink:href="#instance_selector"></use>
            <use xlink:href="#type_selector"></use>
        </svg>
        <!-- <OverviewBox :store="store" :query_string="ui_state.query_string" :hoveredLink="ui_state.hoveredLink">
        </OverviewBox> -->
    </div>
</template>
<script setup lang="ts">
import { ref, watch, reactive, computed, onMounted, onBeforeMount } from 'vue'
import { SubjectNode, Link } from '@/utils/sparql/representation';
import NodeComp from './elements/Node.vue';
import OutLinkSelector from './elements/panels/LinkSelector.vue';
import OverviewBox from './elements/OverviewBox.vue';
import { DisplayMode, InstanceSelectorOpenEvent, LinkEditEvent, OpenEventType, type SelectorOpenEvent } from '@/utils/sparql/helpers';
import InstanceSelector from './elements/panels/InstanceSelector.vue';
import { RepositoryState, type MixedResponse, type NodeLinkRepository } from '@/utils/sparql/store';
import GraphView from './elements/GraphView.vue';
import { OverviewCircles } from '@/utils/three-man/OverviewCircles';
import { fa } from 'vuetify/locale';
import { Api } from '@/api/client.ts/Api';
import { BACKEND_URL } from '@/utils/config';
// import type { SubjectInCircle } from '@/utils/d3-man/CircleMan';

import type { NodeLinkRepositoryDiff } from '@/utils/sparql/diff';
import TypeSelector from './elements/panels/TypeSelector.vue';
import type { PropertiesOpenEvent } from '@/utils/sparql/querymapper';
import LinkComposer from './elements/LinkComposer.vue';
import type { SubjectInCircle } from '@/utils/three-man/CircleMan3D';
import { ViewPortState } from '@/utils/editing';
import { MOUSE } from 'three';

const svg_wrapper = ref<HTMLElement | null>(null)

const api = new Api({
    baseURL: BACKEND_URL
})
const { store, diff, simulate } = defineProps({
    store: {
        type: Object as () => NodeLinkRepository,
        required: true
    },
    diff: {
        type: Object as () => NodeLinkRepositoryDiff | null,
        default: null
    },
    simulate: {
        type: Boolean,
        required: false,
        default: false
    }
})
enum EditorMode {
    EDIT = 'edit',
    CREATE_LINK = 'create_link',
}
const ui_state = reactive({
    hoveredLink: null as Link | null,
    sublink_display: false,
    sublink_event: null as SelectorOpenEvent,
    attaching_display: false,
    attaching_event: null as SelectorOpenEvent,
    instance_display: false,
    instance_event: null as InstanceSelectorOpenEvent,
    type_display: false,
    type_event: null as SelectorOpenEvent,
    run_simulation: false,
    query_string: '',
    editor_mode: EditorMode.EDIT,
    trigger_sim: null as (() => void) | null,
    rect: {
        x: 0,
        y: 0,
        width: 1000,
        height: 500
    },
    viewportState: new ViewPortState(1, { x: 0, y: 0 }),
    viewDragState: {
        dragging: false,
        last: { x: 0, y: 0 },

    }
})

const clickedOutlink = (evt: SelectorOpenEvent) => {
    if (evt.side == OpenEventType.PROP) {
        ui_state.sublink_display = true
        ui_state.sublink_event = evt

        ui_state.attaching_display = false
        ui_state.attaching_event = null
    } else {
        ui_state.editor_mode = EditorMode.CREATE_LINK
        store.state = RepositoryState.EDITING
        ui_state.attaching_display = true
        ui_state.attaching_event = evt

        ui_state.sublink_display = false
        ui_state.sublink_event = null
    }
}
const clickedEditLink = (evt: SelectorOpenEvent) => {
    console.log('clickedEditLink', evt)
    ui_state.editor_mode = EditorMode.EDIT
    store.state = RepositoryState.STABLE
    ui_state.sublink_display = true
    ui_state.sublink_event = evt
}
const clickedInstance = (evt: InstanceSelectorOpenEvent) => {
    ui_state.instance_display = true
    ui_state.instance_event = evt
}
const clickedType = (evt: SelectorOpenEvent) => {
    ui_state.type_display = true
    ui_state.type_event = evt
}
const linkEditDone = (evt: SelectorOpenEvent) => {
    ui_state.sublink_display = true
    ui_state.sublink_event = evt
}

const linkSelectDone = (evt: LinkEditEvent) => {
    ui_state.sublink_display = false
    ui_state.sublink_event = null
    ui_state.attaching_display = false
    ui_state.attaching_event = null
    if (evt.success) {
        ui_state.editor_mode = EditorMode.EDIT
        store.state = RepositoryState.STABLE
        regenerateQuery()
    } else {
        store.removeLink(evt.link)
        if (evt.side != OpenEventType.LINK) {
            store.removeNode(evt.node)
        }
    }
}
const scroll_box = (evt: WheelEvent) => {
    console.log('scroll_box', evt)
    let old_scale = ui_state.viewportState.scale
    ui_state.viewportState.scale *= 1 + evt.deltaY * -0.001
    let diff_scale = ui_state.viewportState.scale - old_scale
    // To keep the zoom centered on the mouse position, we need to adjust the offset based on the mouse position and the change in scale
    const rect = svg_wrapper.value?.getBoundingClientRect()
    if (rect) {
        const mouse_x = evt.clientX - rect.left
        const mouse_y = evt.clientY - rect.top
        ui_state.viewportState.offset.x -= mouse_x * diff_scale / ui_state.viewportState.scale
        ui_state.viewportState.offset.y -= mouse_y * diff_scale / ui_state.viewportState.scale
    }

    evt.preventDefault()
}
const startDrag = (evt: MouseEvent) => {
    if (evt.button == MOUSE.MIDDLE) {
        ui_state.viewDragState.dragging = true
        ui_state.viewDragState.last = { x: evt.clientX, y: evt.clientY }
        // evt.preventDefault()
    }
}
const drag = (evt: MouseEvent) => {
    if (ui_state.viewDragState.dragging) {
        const dx = evt.clientX - ui_state.viewDragState.last.x
        const dy = evt.clientY - ui_state.viewDragState.last.y
        ui_state.viewportState.offset.x += dx / ui_state.viewportState.scale
        ui_state.viewportState.offset.y += dy / ui_state.viewportState.scale
        ui_state.viewDragState.last = { x: evt.clientX, y: evt.clientY }
    }
}
const endDrag = (evt: MouseEvent) => {
    ui_state.viewDragState.dragging = false
}

const regenerateQuery = () => {
    // console.log('Store changed!', store)
    if (!store) {
        return
    }
    let query_string = store.generateQuery()
    // console.log('Query string', query_string)
    if (query_string != ui_state.query_string) {
        ui_state.query_string = query_string
    }
}

watch(() => ui_state.editor_mode, (new_val) => {
    if (ui_state.editor_mode == EditorMode.EDIT) {
        regenerateQuery()
    }
}, { deep: true })
watch(() => store, () => {
    regenerateQuery()
}, { deep: true })
watch(() => store, () => {

    if (simulate) {
        ui_state.run_simulation = true
    }
    if (ui_state.trigger_sim) {
        ui_state.trigger_sim()
    }
}, { deep: false, flush: 'post' })

onMounted(() => {
    let svg_g_rect = svg_wrapper.value?.getBoundingClientRect()
    if (svg_g_rect) {
        ui_state.rect.x = svg_g_rect.x
        ui_state.rect.y = svg_g_rect.y
        ui_state.rect.width = svg_g_rect.width
        ui_state.rect.height = svg_g_rect.height
    }
    // .style('background-color', 'red')

})



</script>
<style lang="scss" scoped>
.query_builder {
    width: 100%;
    height: 100%;
}

.query_build_wrapper {
    width: 100%;
    height: 100%;
    cursor: move;
}

.capture_rect {
    fill: transparent;
    color: transparent;
    pointer-events: all;
}

.node {
    cursor: pointer;
    fill: #ccc;
    stroke: #000;
    stroke-width: 1.5px;

}

.node_text {
    font-size: 10px;
    text-anchor: middle;
}

</style>