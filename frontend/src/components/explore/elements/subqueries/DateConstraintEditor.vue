<template>
    <div class="constraint">
        <div class="constraint_label">{{ constraint.link.label }}</div>
        <div>
            <span class="constraint_select"><select @change="change_operator" :value="constraint.type">
                    <option v-for="option in operator_options" :value="option.value">{{ option.label }}</option>
                </select></span><span><input type="date" v-model="date_value" class="constraint_input"></span>
        </div>
    </div>
</template>
<script setup lang="ts">
import { SubQuery, DateConstraint, NumberConstraint, NumberConstraintType, StringConstraint, StringConstraintType } from '@/utils/sparql/representation';
import { defineProps, defineModel, computed, ref, watch } from 'vue'

const { constraint } = defineProps({
    constraint: {
        type: Object as () => DateConstraint,
        required: true
    }
})
console.log('DateConstraintEditor', constraint)
const date_value = ref(constraint.value ? constraint.value.toISOString().split('T')[0] : "")

const operator_options = [
    { value: NumberConstraintType.EQUALS, label: '=' },
    { value: NumberConstraintType.GREATER, label: '>' },
    { value: NumberConstraintType.LESS, label: '<' },
]
const change_operator = (event: Event) => {
    const target = event.target as HTMLSelectElement
    constraint.type = target.value as NumberConstraintType
}
watch(() => date_value, () => {
    // console.log('date_value changed!', date_value.value)
    constraint.value = new Date(date_value.value)
}, { deep: true })
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
