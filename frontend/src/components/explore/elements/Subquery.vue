<template>
    <g>
        <path :d="`M 0,-${extend_path} v ${extend_path}`" class="subquery_connection" />
        <path :d="`M 0,0 V ${subquery.height / 2} H ${subquery.width * 0.2}`" class="subquery_connection" />
        <rect :x="subquery.width * 0.2" :y="0" :width="subquery.width * 0.8" :height="subquery.height"
            class="subquery_box" :class="query_statestyle" />
        <circle v-show="show_editpoints && mode == DisplayMode.EDIT" :cx="subquery.width" :cy="0" :r="7"
            class="edit_point edit_point_delete" @click="emit('delete', subquery)">
        </circle>
        <foreignObject :x="subquery.width * 0.2" :y="0" :width="subquery.width * 0.8" :height="subquery.height">
            <div class="subquery">
                <!-- {{ constraint.link.to_proptype }} -->
                <NumberConstraintEditor v-if="(subquery.constraint_type == SubQueryType.NUMBER)"
                    :constraint="(subquery as NumberConstraint)" />
                <StringConstraintEditor v-if="(subquery.constraint_type == SubQueryType.STRING)"
                    :constraint="(subquery as StringConstraint)" />
                <DateConstraintEditor v-if="(subquery.constraint_type == SubQueryType.DATE)"
                    :constraint="(subquery as DateConstraint)" />
                <SubjectConstraintEditor v-if="(subquery.constraint_type == SubQueryType.SUBJECT)"
                    :constraint="(subquery as SubjectConstraint)" :node="node"
                    @open_search="emit('instanceSearchClicked', $event)" />
                <BooleanConstraintEditor v-if="(subquery.constraint_type == SubQueryType.BOOLEAN)"
                    :constraint="(subquery as BooleanConstraint)" />
                <Property v-if="(subquery.constraint_type == SubQueryType.QUERY_PROP)"
                    :query="(subquery as QueryProp)" />
                <VectorSubquery v-if="(subquery.constraint_type == SubQueryType.VECTOR_SORT)"
                    :constraint="(subquery as VectorSort)" />
            </div>
        </foreignObject>
    </g>
</template>
<script setup lang="ts">
import { SubQuery, SubQueryType, DateConstraint, SubjectNode, NumberConstraint, StringConstraint, SubjectConstraint, BooleanConstraint, QueryProp, NodeState, VectorSort } from '@/utils/sparql/representation';
import { defineProps, defineModel, computed, reactive, watch } from 'vue'
import NumberConstraintEditor from './subqueries/NumberConstraintEditor.vue';
import StringConstraintEditor from './subqueries/StringConstraintEditor.vue';
import DateConstraintEditor from './subqueries/DateConstraintEditor.vue';
import SubjectConstraintEditor from './subqueries/SubjectConstraintEditor.vue';
import { DisplayMode, type InstanceSelectorOpenEvent } from '@/utils/sparql/helpers';
import BooleanConstraintEditor from './subqueries/BooleanConstraintEditor.vue';
import VectorSubquery from './subqueries/VectorSubquery.vue';
import Property from './Property.vue';
import type { NodeDiff } from '@/utils/sparql/diff';
const emit = defineEmits<{
    delete: [value: SubQuery]
    instanceSearchClicked: [value: InstanceSelectorOpenEvent]
}>()
const { extend_path, subquery: subquery, diff } = defineProps({
    extend_path: {
        type: Number,
        required: true
    },
    subquery: {
        type: Object as () => SubQuery,
        required: true
    },
    node: {
        type: Object as () => SubjectNode,
        required: true
    },
    show_editpoints: {
        type: Boolean,
        required: true
    },
    diff: {
        type: Object as () => NodeDiff | null,
        default: null
    },
    mode: {
        type: String as () => DisplayMode,
        default: DisplayMode.SELECT
    },
})
const editor_data = reactive({
    state: null as NodeState | null
})
const updateNodeState = () => {
    if (diff) {
        let diff_node_added = diff.diff_subqueries.added.find((sq) => sq.right.id == subquery.id)
        if (diff_node_added) {
            editor_data.state = NodeState.ADDED
            return
        }
        let diff_node_del = diff.diff_subqueries.removed.find((sq) => sq.left.id == subquery.id)
        if (diff_node_del) {
            editor_data.state = NodeState.REMOVED
            return
        }
        if (diff.diff_subqueries.changed.find((sq) => sq.left.id == subquery.id)) {
            editor_data.state = NodeState.CHANGED
            return
        }
    }
    editor_data.state = NodeState.NORMAL
}
watch(() => diff, () => {
    updateNodeState()
}, { immediate: true, deep: true })
const query_statestyle = computed(() => {
    // console.log('subject.state', subject.state)
    let state = editor_data.state.toLowerCase()
    if (!state) {
        return ''
    }
    return `node_${state.toLowerCase()}`
})

</script>
<style lang="scss" scoped>
.subquery_connection {
    fill: none;
    stroke: #828282;
    stroke-width: 1px;
}

.subquery_box {
    // fill: #dfdfdf;
    stroke: #a0c2a9;
    stroke-width: 1px;
    stroke-dasharray: 5, 5;
}

.subquery {
    width: 100%;
    height: 100%;
    display: flex;
    align-items: center;
    justify-content: center;
    // justify-items: center;

}
</style>
