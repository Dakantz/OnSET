<template>
    <div class="constraint">
        <div class="constraint_label">is</div>
        <div class="constraint_select">{{ readableName(constraint.instance?.id, constraint.instance?.label) }}</div>
        <OnsetBtn @click="emits('open_search', {
            constraint: constraint,
            node: node
        })" :btn_height="'1.5rem'" :btn_width="'100%'" :toggleable="false">Choose</OnsetBtn>
    </div>
</template>
<script setup lang="ts">
import OnsetBtn from '@/components/ui/OnsetBtn.vue';
import { CONSTRAINT_HEIGHT, type InstanceSelectorOpenEvent } from '@/utils/sparql/helpers';
import { readableName } from '@/utils/sparql/querymapper';
import { SubQuery, SubjectNode, StringConstraint, StringConstraintType, SubjectConstraint } from '@/utils/sparql/representation';
import { defineProps, defineModel, computed, defineEmits, watch } from 'vue'
const emits = defineEmits<{
    open_search: [value: InstanceSelectorOpenEvent]
}>()
const { constraint } = defineProps({
    constraint: {
        type: Object as () => SubjectConstraint,
        required: true
    },
    node: {
        type: Object as () => SubjectNode,
        required: true
    },
})
watch(() => constraint.instance, (instance) => {
    if (constraint.instance) {
        constraint.height = CONSTRAINT_HEIGHT
    }
})
const selection_display_width = computed(() => {
    return constraint.instance ? '70%' : '30%'
})
</script>
<style lang="scss" scoped>
.constraint {
    display: flex;
    flex-wrap: wrap;
    justify-items: center;
    align-items: center;
    flex-direction: row;
}

.constraint_label {
    margin-right: 3px;
}

.constraint_select {
    margin-right: 3px;
    border: rgb(105, 132, 99) 1px solid;
    // display: flex;
    width:  v-bind("selection_display_width");;
    max-height: 2rem;
    overflow: hidden;
    justify-content: center;
    align-content: center;
}

.constraint_input {
    border: rgb(105, 132, 99) 1px solid;
    border-radius: 0px;
}
</style>
