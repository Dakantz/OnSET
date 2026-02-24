<template>
    <g>
        <g :transform="`translate(${subject.x},${subject.y})`" @mouseout.capture="editPointHover($event, false)"
            @mouseenter.capture="editPointHover($event, true)" @mouseover="editPointHover($event, true)">
            <rect :x="`${-7}px`" :y="`${-7}px`"
                :width="`${subject.width + editor_data.editpoint_r * 2 + (constraint_list_mapped.length > 0 ? CONSTRAINT_WIDTH : 0)}px`"
                :height="`${constraints_height + subject.height + editor_data.editpoint_r * 2}px`" fill-opacity="0">

            </rect>
            <rect :width="`${subject.width}px`" :height="`${subject.height}px`" class="node" :class="node_statestyle"
                @mousedown="mouseDownNode" @mousemove="mouseMoveNode" @mouseup="mouseUpNode" @mouseleave="mouseUpNode">
            </rect>

            <text :x="`${subject.width / 2}px`" :y="`${subject.height / 2}px`" class=node_text>
                {{ (mode == DisplayMode.RESULTS || mode == DisplayMode.RESULT_INTERACTIVE) ?
                    result_subject.instance_label :
                    subject.label }}
            </text>
            <g v-if="mode == DisplayMode.EDIT || mode == DisplayMode.SELECT"
                v-for="constr_info in constraint_list_mapped"
                :transform="`translate(${subject.width / 2},${constr_info.y})`">
                <Sublink :subquery="constr_info.subquery" :extend_path="constr_info.extend_path" :diff="diff_node"
                    :show_editpoints="editor_data.show_editpoints" :node="subject" @delete="deleteConstraint"
                    :mode="mode" @instance-search-clicked="emit('instanceSearchClicked', $event)">

                </Sublink>
            </g>

            <g v-show="mode == DisplayMode.RESULT_INTERACTIVE && editor_data.show_editpoints">
                <circle :cx="subject.width / 2" :cy="subject.height" :r="editor_data.editpoint_r"
                    class="edit_point edit_point_prop"
                    @click="emit('propPointClicked', { node: subject as InstanceNode })"></circle>
            </g>
            <g v-show="mode == DisplayMode.EDIT && editor_data.show_editpoints">
                <circle :cx="0" :cy="subject.height / 2" :r="editor_data.editpoint_r" class="edit_point edit_point_link"
                    @click="emit('linkPointClicked', { side: OpenEventType.FROM, node: subject, evt: $event })">
                </circle>
                <text :x="`${-editor_data.editpoint_r}px`" :y="`${subject.height / 2}px`"
                    class="help_text_left">From</text>

                <circle :cx="subject.width / 2" :cy="constraints_height + subject.height" :r="editor_data.editpoint_r"
                    class="edit_point edit_point_prop"
                    @click="emit('linkPointClicked', { side: OpenEventType.PROP, node: subject, evt: $event })">
                </circle>
                <text :x="`${subject.width / 2}px`" :y="`${subject.height + editor_data.editpoint_r * 3}px`"
                    class="help_text_bottom">Constraint/Property</text>

                <circle :cx="subject.width" :cy="subject.height / 2" :r="editor_data.editpoint_r"
                    @click="emit('linkPointClicked', { side: OpenEventType.TO, node: subject, evt: $event })"
                    class="edit_point edit_point_link">
                </circle>
                <text :x="`${subject.width + editor_data.editpoint_r}px`" :y="`${subject.height / 2}px`"
                    class="help_text_right">To</text>

                <circle :cx="subject.width / 2" :cy="0" :r="editor_data.editpoint_r"
                    @click="emit('typePointClicked', { side: OpenEventType.TO, node: subject, evt: $event })"
                    class="edit_point edit_point_type">
                </circle>
                <text :x="`${subject.width / 2}px`" :y="`${-editor_data.editpoint_r * 3}px`"
                    class="help_text_top">Specify</text>

                <circle :cx="subject.width" :cy="0" :r="editor_data.editpoint_r" @mouseover="hoverDeletion(true)"
                    @mouseout="hoverDeletion(false)" class="edit_point edit_point_delete" @click="doDeletion()">
                </circle>

            </g>
        </g>
    </g>
</template>
<script setup lang="ts">
import { ref, watch, reactive, computed, onMounted, onBeforeUpdate, type Prop, onUpdated, onRenderTriggered } from 'vue'
import { InstanceNode, SubjectNode as NodeRepr, NodeState, SubQuery } from '@/utils/sparql/representation';
import { CONSTRAINT_PADDING, CONSTRAINT_WIDTH, DisplayMode, InstanceSelectorOpenEvent, OpenEventType, SelectorOpenEvent } from '@/utils/sparql/helpers';
import Sublink from './Subquery.vue';
import type { PropertiesOpenEvent } from '@/utils/sparql/querymapper';
import type { NodeLinkRepository } from '@/utils/sparql/store';
import type { NodeLinkRepositoryDiff } from '@/utils/sparql/diff';

const emit = defineEmits<{
    linkPointClicked: [value: SelectorOpenEvent]
    propPointClicked: [value: PropertiesOpenEvent]
    typePointClicked: [value: SelectorOpenEvent]
    instanceSearchClicked: [value: InstanceSelectorOpenEvent]
}>()

const { subject, mode, store, diff, scale } = defineProps({
    subject: {
        type: Object as () => NodeRepr,
        required: true
    },
    store: {
        type: Object as () => NodeLinkRepository,
        required: true
    },
    mode: {
        type: String as () => DisplayMode,
        default: DisplayMode.SELECT
    },
    diff: {
        type: Object as () => NodeLinkRepositoryDiff | null,
        default: null
    },
    scale: {
        type: Number,
        default: 1
    }
})
const editor_data = reactive({
    mouse_down: false,
    mouse_x: 0,
    mouse_y: 0,
    constraint_padding: 5,
    show_editpoints: false,
    editpoint_r: 7,
    hover_deletion: false,
    state: NodeState.NORMAL
})
const mouseDownNode = (event: MouseEvent) => {
    if (mode == DisplayMode.EDIT || mode == DisplayMode.RESULT_INTERACTIVE || mode == DisplayMode.EDIT_NO_ADD) {
        editor_data.mouse_down = true
        editor_data.mouse_x = event.clientX
        editor_data.mouse_y = event.clientY
    }
}
const mouseUpNode = (event: MouseEvent) => {
    editor_data.mouse_down = false
}
const mouseMoveNode = (event: MouseEvent) => {
    if (editor_data.mouse_down) {
        subject.x += (event.clientX - editor_data.mouse_x) / scale
        subject.y += (event.clientY - editor_data.mouse_y) / scale
        editor_data.mouse_x = event.clientX
        editor_data.mouse_y = event.clientY
    }
}
class SubQueryDisplay {
    subquery: SubQuery | null = null
    y: number = 0
    extend_path: number = 0
    constructor(subquery: SubQuery, state: NodeState = NodeState.NORMAL) {
        this.subquery = subquery
    }
}
const constraint_list_mapped = computed(() => {
    if (!subject.subqueries) {
        return []
    }

    let constraints = subject.subqueries.filter(constr => constr != null).map((subquery) => new SubQueryDisplay(subquery))
    if (diff_node.value) {
        constraints = constraints.concat(diff_node.value.diff_subqueries.removed.map((subquery) => new SubQueryDisplay(subquery.left, NodeState.REMOVED)))
    }
    constraints = constraints.concat()
    // if (constraints.length > 0) {
    //     constraints[0].first_prop = true
    // }
    let y_pos = subject.height + CONSTRAINT_PADDING
    let last_height = 0
    for (let constr of constraints) {
        constr.y = y_pos
        y_pos += constr.subquery.height + CONSTRAINT_PADDING
        if (last_height == 0) {
            constr.extend_path = CONSTRAINT_PADDING
        } else {
            constr.extend_path = last_height / 2 + CONSTRAINT_PADDING
        }
        last_height = constr.subquery.height
    }
    return constraints
})
const constraints_height = computed(() => {
    return constraint_list_mapped.value.reduce((acc, constr) => acc + constr.extend_path + constr.subquery.height / 2, 0)
})
watch(() => diff, () => {
    updateNodeState()
}, {
    deep: true
})
watch(() => subject.state, () => {
    updateNodeState()
}, { deep: true })
watch(() => editor_data.hover_deletion, () => {
    if (!store) {
        return
    }
    let target_state = editor_data.hover_deletion ? NodeState.DELETION_IMMINENT : NodeState.NORMAL
    subject.state = target_state
}, { deep: true })

const node_statestyle = computed(() => {
    // console.log('subject.state', subject.state)
    let state = editor_data.state.toLowerCase()
    if (!state) {
        return ''
    }
    return `node_${state.toLowerCase()}`
})
const diff_node = computed(() => {
    if (diff) {
        let diff_node_added = diff.diff_nodes.added.find((node) => node.right.internal_id == subject.internal_id)
        if (diff_node_added) {
            return diff_node_added
        }
        let diff_node_removed = diff.diff_nodes.removed.find((node) => node.left.internal_id == subject.internal_id)
        if (diff_node_removed) {
            return diff_node_removed
        }
        let diff_node_changed = diff.diff_nodes.changed.find((node) => node.left.internal_id == subject.internal_id)
        if (diff_node_changed) {
            return diff_node_changed
        }

    }
    return null
})

const updateNodeState = () => {
    if (subject.state == NodeState.DELETION_IMMINENT) {
        editor_data.state = NodeState.DELETION_IMMINENT
        return
    }
    if (diff) {
        let diff_node = diff.diff_nodes.added.find((node) => node.right.internal_id == subject.internal_id)
        if (diff_node) {
            editor_data.state = NodeState.ADDED
            return
        }
        let diff_node_del = diff.diff_nodes.removed.find((node) => node.left.internal_id == subject.internal_id)
        if (diff_node_del) {
            editor_data.state = NodeState.REMOVED
            return
        }
    }
    editor_data.state = NodeState.NORMAL
}

const hoverDeletion = (state: boolean) => {
    editor_data.hover_deletion = state
}
const doDeletion = () => {
    store.removeNode(subject)
}
const editPointHover = (event: MouseEvent, state: boolean) => {
    editor_data.show_editpoints = state
}
const deleteConstraint = (constraint) => {
    subject.subqueries = subject.subqueries.filter((constr) => constr != constraint)
}
const result_subject = computed(() => subject as InstanceNode)
onMounted(() => {
    // console.log('subject', subject)
    updateNodeState()
})
</script>
<style lang="scss">
.node {
    cursor: pointer;
    // fill: #ccc;
    stroke: #000;
    stroke-width: 1.5px;

}

.node_deletion_imminent {
    fill: #f2b56c;
    stroke-dasharray: 5, 5;
}

.node_text {
    font-size: 10px;
    text-anchor: middle;
    pointer-events: none;
}

.edit_point {
    fill: #a0c2a9;
    cursor: pointer;
    fill-opacity: 0.4;
}

.edit_point:hover {
    stroke: #888888;
    display: block;
    fill-opacity: 1;
}

.edit_point_delete {
    fill: #ea694f;
}

.edit_point_prop {
    fill: #a0c2a9;

}

.edit_point_link {
    fill: #c2bca0;
}

.edit_point_type {
    fill: #6be1ff;
}

@mixin help_text($anchor: middle, $baseline: 0.5em) {
    font-size: 10px;
    text-anchor: $anchor;
    dominant-baseline: central;
}

.help_text_right {
    @include help_text(start);
}

.help_text_top {
    @include help_text(middle, 1.5em);
}

.help_text_bottom {
    @include help_text(middle, -0.5em);
}

.help_text_left {
    @include help_text(end);
}
</style>