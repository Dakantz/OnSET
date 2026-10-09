<template>
    <div class="constraint">
        <span class="constraint_label">{{ constraint.link.label }}</span><span><select @change="change_operator" class="constraint_select" :value="constraint.type">
                <option v-for="option in operator_options" :value="option.value">{{ option.label }}</option>
            </select></span><span><input class="constraint_input" type="number" v-model="constraint.value"></span>
    </div>
</template>
<script setup lang="ts">
import { SubQuery, NumberConstraint, NumberConstraintType } from '@/utils/sparql/representation';
import { defineProps, defineModel, computed } from 'vue'

const { constraint } = defineProps({
    constraint: {
        type: Object as () => NumberConstraint,
        required: true
    }
})
const operator_options = [
    { value: NumberConstraintType.EQUALS, label: '=' },
    { value: NumberConstraintType.GREATER, label: '>' },
    { value: NumberConstraintType.LESS, label: '<' },
]
const change_operator = (event: Event) => {
    const target = event.target as HTMLSelectElement
    constraint.type = target.value as NumberConstraintType
}
</script>
<style lang="scss" scoped>
.constraint_label {
    margin-right: 5px;
}
.constraint_select {
    margin-right: 5px;
    border: rgb(105, 132, 99) 1px solid;
    border-radius: 0px;

}
.constraint_input {
    width: 50px;
    border: rgb(105, 132, 99) 1px solid;
    border-radius: 0px;
}
</style>
