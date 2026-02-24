<template>
    <div class="result_plot_wrapper">


        <div v-if="combined_stores.instances.length > 0" class="result_instance_element"
            v-for="s of combined_stores.instances">
            <Result :store="jsonClone(s)" :expanded="false" :scale="ui_state.scale" :offset="ui_state.offset"
                :miniature-type="miniatureType(s)" :diff="diff">
            </Result>
        </div>
        <div v-else class="result_instance_element" v-for="s of mapped_stores.instances">
            <Result :store="jsonClone(s)" :expanded="false" :scale="ui_state.scale" :offset="ui_state.offset">
            </Result>
        </div>
        <Loading v-if="ui_state.loading"></Loading>
        <OnsetBtn v-if="mapped_stores.instances.length > 0 && !ui_state.paging_end" @click="loadMore" btn_width="100%"
            :toggleable="false">Load more</OnsetBtn>
        <div class="result_instance_element" ref="view_container" v-show="mapped_stores.instances.length == 0">
        </div>
    </div>
</template>
<script setup lang="ts">
import { ref, watch, reactive, onMounted } from 'vue'
import { InstanceNodeLinkRepository, PropertiesOpenEvent, QueryMapper, ResultList } from '@/utils/sparql/querymapper';
import { Vector2 } from 'three';
import Loading from '../../ui/Loading.vue';
import Result from './Miniature.vue';
import OnsetBtn from '../../ui/OnsetBtn.vue';
import type { NodeLinkRepository } from '@/utils/sparql/store';
import { ResultListDiff, type NodeLinkRepositoryDiff } from '@/utils/sparql/diff';
import { instance } from 'three/webgpu';
import { MiniatureType } from '@/utils/result-plot/plot-types';
import { jsonClone } from '@/utils/parsing';
const { store, query_string, diff } = defineProps({
    store: {
        type: Object as () => NodeLinkRepository,
        required: true
    },
    query_string: {
        type: String,
        required: true
    },
    diff: {
        type: Object as () => NodeLinkRepositoryDiff | null,
        default: null
    }
})
const mapper = ref(null as QueryMapper | null)
const mapped_stores = ref(new ResultList())

const store_cache = ref(new Map<string, ResultList>())
const combined_stores = ref(new ResultList())
const results_diff = ref(null as ResultListDiff | null)

const view_container = ref(null as SVGSVGElement | null)
const ui_state = reactive({
    loading: false,
    last_query_id: 0,
    scale: 1,
    offset: new Vector2(0, 0),
    initial_size: new Vector2(0, 0),
    computed_size: new Vector2(0, 0),
    prop_open: false,
    prop_open_event: null as PropertiesOpenEvent | null,
    paging_offset: 0,
    paging_end: false,
})
const startLoading = () => {
    if (!store) {
        return
    }
    mapper.value = new QueryMapper(store, ui_state.initial_size)
    mapper.value.target_size = ui_state.computed_size
    ui_state.paging_offset = 0
    ui_state.paging_end = false
    mapped_stores.value = new ResultList()
    loadMore().catch((err) => {
        console.error('Error while mapping query!', err)
        ui_state.loading = false
    })
}
watch(() => query_string, () => {
    startLoading()
}, { deep: true })
const updateSize = () => {
    if (view_container.value) {
        let rect = view_container.value.getBoundingClientRect()

        ui_state.computed_size.x = rect.width || 0
        ui_state.computed_size.y = rect.height || 0
    }
    console.log("Updated size:", ui_state.computed_size)
    mapper.value.target_size = ui_state.computed_size
}
const miniatureType = (s: InstanceNodeLinkRepository) => {
    // console.log('Diff!', s, results_diff.value.diff_instances)
    if (diff) {
        if (results_diff.value.diff_instances.removed.find((r) => r.left.id == s.id)) {
            // console.log('Left removed!', s)
            return MiniatureType.LEFT
        } else if (results_diff.value.diff_instances.added.find((r) => r.right.id == s.id)) {
            // console.log('Right added!', s)
            return MiniatureType.RIGHT
        }
    }
    return MiniatureType.BOTH
}
const loadMore = async () => {
    let query_id = ui_state.last_query_id + 1
    ui_state.last_query_id = query_id
    ui_state.loading = true
    const retrieved_stores = await mapper.value.runAndMap(query_string, ui_state.paging_offset)
    updateSize()

    const scalings = mapper.value.scalingFactors()
    // console.log('Mapped results!', mapped_stores, query_id, ui_state.last_query_id)
    if (query_id == ui_state.last_query_id) {
        ui_state.scale = scalings.scale
        ui_state.offset = new Vector2(scalings.offset.x, scalings.offset.y)
        ui_state.computed_size = new Vector2(scalings.size.x, scalings.size.y)

        ui_state.paging_offset += retrieved_stores.instances.length
        mapped_stores.value.instances = mapped_stores.value.instances.concat(retrieved_stores.instances)
        let current_query_string = store.generateQuery()
        store_cache.value.set(current_query_string, retrieved_stores)
        if (diff) {
            let old_query_string = diff.left.generateQuery()
            let old_stores = store_cache.value.get(old_query_string)
            if (old_stores) {
                results_diff.value = new ResultListDiff(mapped_stores.value, old_stores)
                combined_stores.value = new ResultList(
                    mapped_stores.value.instances.concat(old_stores.instances).sort((a, b) => {
                        return a.id.toString().localeCompare(b.id.toString())
                    }),
                )
            }
        }

        if (retrieved_stores.instances.length == 0) {
            ui_state.paging_end = true
        }
        ui_state.loading = false

    }
}
watch(() => diff, () => {
    if (!diff) {
        combined_stores.value = new ResultList()
        results_diff.value = null
    }
}, { deep: true })
onMounted(() => {
    startLoading()
})
</script>
<style lang="scss">
.results_instance_container {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: flex-start;
    width: 100%;
    height: 100%;
    overflow: auto;
    padding: 5px;
    margin-top: 10px;
}

.result_instance_element {
    max-width: 95%;
    max-height: 20%;

    height: 10vh;
    display: flex;
    justify-content: center;
    align-items: center;
    margin: 4px;
}

.result_instance_svg {
    width: 100%;
    height: 100%;
}

.result_interact_svg {
    width: 100%;
    height: 100%;
}
</style>
