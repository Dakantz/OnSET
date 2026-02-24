<template>
    <g v-if="propDragData.drag" class="link-composer" @mousedown="stopPropDrag()" @mousemove="mouse_move($event)">
        <rect :x="`${extent.x}px`" :y="`${extent.y}px`" :width="`${extent.width}px`" :height="`${extent.height}px`"
            fill="transparent">
        </rect>
        <LinkComp :link="propDragData.dragged_link" :store="propDragData.drag_store" :display_mode="DisplayMode.SELECT"
            :circular="propDragData.circular" />
        <NodeComp v-if="!propDragData.attaching_to" :subject="propDragData.dragged_node"
            :store="propDragData.drag_store" :display_mode="DisplayMode.SELECT" />
    </g>
</template>
<script setup lang="ts">
import { reactive, watch, computed } from 'vue'

import { Link, NodeState, SubjectNode } from '@/utils/sparql/representation';
import { NodeLinkRepository } from '@/utils/sparql/store';
import { DisplayMode, InstanceSelectorOpenEvent, OpenEventType, SelectorOpenEvent } from '@/utils/sparql/helpers';
import NodeComp from './Node.vue';
import LinkComp from './Link.vue';
import { jsonClone } from '@/utils/parsing';
import { extentNodes } from '../../../utils/sparql/helpers';
import { ViewPortState } from '@/utils/editing';


const emit = defineEmits<{
    (e: 'selectionComplete', value: SelectorOpenEvent): void
}>()

const props = defineProps<{
    store: NodeLinkRepository,
    evt: SelectorOpenEvent | null,
    viewport: ViewPortState
}>()

const propDragData = reactive({
    drag: false,
    dragged_link: null as Link | null,
    dragged_node: null as SubjectNode | null,
    drag_store: null as NodeLinkRepository | null,
    attaching_to: null as SubjectNode | null,
    circular: false,
})
watch(() => props.evt, (evt) => {
    console.log("LinkComposer watch", evt)
    if (evt) {
        startPropDrag(evt)
    }
}, { immediate: true })
const startPropDrag = (evt: SelectorOpenEvent) => {
    if (!props.evt) {
        return;
    }
    propDragData.drag = true
    propDragData.dragged_node = new SubjectNode({
        subject_id: "dragged_node",
        label: "",
    })
    let start_node = jsonClone(evt.node);
    let from_node,
        to_node;
    if (evt.side == OpenEventType.TO) {
        from_node = start_node
        to_node = propDragData.dragged_node
    } else {
        from_node = propDragData.dragged_node
        to_node = start_node
    }
    propDragData.drag_store = Link.betweenNodes(from_node, to_node)
    propDragData.dragged_link = propDragData.drag_store.links[0]
    console.log("LinkComposer startPropDrag", from_node, to_node, evt)
    mouse_move(evt.evt)
}

const extent = computed(() => {
    let nodes = [...props.store.nodes, propDragData.dragged_node];
    return extentNodes(nodes)
})
const mouse_move = (event: MouseEvent) => {
    if (propDragData.drag) {
        // Update the position of the dragged link and node based on mouse position
        const x = event.offsetX / props.viewport.scale - props.viewport.offset.x;
        const y = event.offsetY / props.viewport.scale - props.viewport.offset.y;
        let offsetX = 0;
        let offsetY = 0;
        if (props.evt.side == OpenEventType.TO) {
            offsetY = -props.evt.node.height / 2;
        } else {
            offsetX = -props.evt.node.width;
            offsetY = -props.evt.node.height / 2;
        }
        propDragData.dragged_node.x = x + offsetX;
        propDragData.dragged_node.y = y + offsetY;
        const hovering_node = props.store.nodes.find(n =>
            n.x <= x && n.x + n.width >= x &&
            n.y <= y && n.y + n.height >= y
        )
        if (hovering_node) {
            hovering_node.state = NodeState.ATTACHING
            propDragData.attaching_to = hovering_node
            propDragData.dragged_node.x = hovering_node.x
            propDragData.dragged_node.y = hovering_node.y
            if (propDragData.attaching_to.internal_id == props.evt.node.internal_id) {
                propDragData.circular = true
                console.log("Circular link detected", propDragData.attaching_to.internal_id, props.evt.node.internal_id)
            } else {
                propDragData.circular = false
            }
        } else {
            if (propDragData.attaching_to) {
                propDragData.attaching_to.state = NodeState.NORMAL
            }
            propDragData.attaching_to = null
            propDragData.circular = false
        }
    }

}
const stopPropDrag = () => {
    if (propDragData.attaching_to) {
        propDragData.attaching_to.state = NodeState.NORMAL
    }
    if (propDragData.dragged_link && propDragData.dragged_node) {
        if (!propDragData.attaching_to) {
            props.store.nodes.push(propDragData.dragged_node)
        } else {
            if (props.evt.side == OpenEventType.TO) {
                propDragData.dragged_link.to_internal_id = propDragData.attaching_to.internal_id
                propDragData.dragged_link.to_id = propDragData.attaching_to.subject_id
            } else {
                propDragData.dragged_link.from_internal_id = propDragData.attaching_to.internal_id
                propDragData.dragged_link.from_id = propDragData.attaching_to.subject_id
            }
        }
        props.store.links.push(propDragData.dragged_link)
        console.log("LinkComposer selection complete", propDragData.attaching_to, propDragData.dragged_node, propDragData.dragged_link)

        const evt: SelectorOpenEvent = {
            side: propDragData.attaching_to ? OpenEventType.LINK : props.evt.side,
            node: propDragData.attaching_to || propDragData.dragged_node,
            link: propDragData.dragged_link,
            evt: null
        }
        emit('selectionComplete', evt)
    }
    propDragData.drag = false
    propDragData.dragged_link = null
    propDragData.dragged_node = null
    propDragData.drag_store = null
}
</script>

<style scoped lang="scss"></style>