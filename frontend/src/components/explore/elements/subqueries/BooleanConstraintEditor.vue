<template>
    <div class="constraint">
        <span class="constraint_label">{{ constraint.link.label }}</span><span><input class="constraint_input"
                type="checkbox" v-model="constraint.value"></span>
    </div>
</template>
<script setup lang="ts">
import { SubQuery, BooleanConstraint } from '@/utils/sparql/representation';
import { defineProps, defineModel, computed } from 'vue'

const { constraint } = defineProps({
    constraint: {
        type: Object as () => BooleanConstraint,
        required: true
    }
})
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
