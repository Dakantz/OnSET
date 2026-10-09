<template>
    <div class="constraint">
        <div class="constraint_label">{{ constraint.link.label }}</div>
        <div>
            <span> Modality: </span>
            <span class="constraint_select"><select @change="change_operator" :value="constraint.modality">
                    <option v-for="option in operator_options" :value="option.value">{{ option.label }}</option>
                </select></span><span>
                <div v-if="constraint.modality == VectorSortModality.TEXT">
                    <span>Text: </span>
                    <input v-model="constraint.input_state.text" class="constraint_input">
                </div>
                <div v-if="constraint.modality == VectorSortModality.IMAGE">
                    <span>Draw your search!</span>
                    <PictureDrawer v-model="constraint.input_state.image" />
                </div>
            </span>
        </div>
    </div>

</template>
<script setup lang="ts">
import { Api } from '@/api/client.ts/Api';
import PictureDrawer from '@/components/ui/PictureDrawer.vue';
import { BACKEND_URL } from '@/utils/config';
import { debounce } from '@/utils/helpers';
import { VectorSort, VectorSortModality } from '@/utils/sparql/representation';
import { defineProps, reactive, watch } from 'vue'

const api = new Api({
    baseURL: BACKEND_URL
})
const { constraint } = defineProps({
    constraint: {
        type: Object as () => VectorSort,
        required: true
    }
})


const editor_data = reactive({
    loading: false,
    error: null as string | null,
})

const operator_options = [
    { value: VectorSortModality.TEXT, label: 'Text' },
    { value: VectorSortModality.IMAGE, label: 'Image' },
]
const change_operator = (event: Event) => {
    const target = event.target as HTMLSelectElement
    constraint.input_state.text = ""
    constraint.input_state.image = null
    constraint.modality = target.value as VectorSortModality
}
watch(() => constraint.input_state.text, () => {
    debounced_vector_refresh()
})
watch(() => constraint.input_state.image, () => {
    debounced_vector_refresh()
})

const debounced_vector_refresh = debounce(() => {
    (async () => {
        editor_data.loading = true
        await constraint.reloadVectorFromState(api)
    })().catch((e) => {
        console.error('Error fetching selection options', e)
    }).finally(() => {
        editor_data.loading = false
    })
}, 300, false)
</script>
<style lang="scss" scoped>
.constraint {
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
    width: calc(100% - 4em);
    border: rgb(105, 132, 99) 1px solid;
    border-radius: 0px;
}
</style>
