<template>
    <div class="constraint">
        <div class="constraint_label">{{ constraint.link.label }}</div>
        <div>
            <span class="constraint_select"><select @change="change_operator" :value="constraint.type">
                <option v-for="option in operator_options" :value="option.value">{{ option.label }}</option>
            </select></span><span><input v-model="constraint.value" class="constraint_input"></span>
        </div>
    </div>
</template>
<script setup lang="ts">
import { SubQuery, StringConstraint, StringConstraintType } from '@/utils/sparql/representation';
import { defineProps, defineModel, computed } from 'vue'

const { constraint } = defineProps({
    constraint: {
        type: Object as () => StringConstraint,
        required: true
    }
})
const operator_options = [
    { value: StringConstraintType.EQUALS, label: '=' },
    { value: StringConstraintType.NEQUALS, label: '!=' },
    { value: StringConstraintType.CONTAINS, label: 'contains' },
    { value: StringConstraintType.ENDSWITH, label: 'ends with' },
    { value: StringConstraintType.STARTSWITH, label: 'starts with' },
    { value: StringConstraintType.REGEX, label: 'matches regex' },
]
const change_operator = (event: Event) => {
    const target = event.target as HTMLSelectElement
    constraint.type = target.value as StringConstraintType
}
</script>
<style lang="scss" scoped>
.constraint{
    display: flex;
    justify-items: start;
    align-items: start;
    flex-direction: column;
    padding: 5px;
}

.constraint_label {
    margin-right: 3px;
}
.constraint_select {
    margin-right: 3px;
    border: rgb(105, 132, 99) 1px solid;
    border-radius: 0px;

}
.constraint_input {
    width: 60px;
    border: rgb(105, 132, 99) 1px solid;
    border-radius: 0px;
}
</style>
