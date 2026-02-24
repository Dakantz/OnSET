<template>
    <div class="results_view">
        <div class="result_instance_header">Results</div>

        <SelectorGroup v-model="ui_state.result_mode" :options="Object.keys(ResultMode).map(qm => {
            return { value: ResultMode[qm], label: ResultMode[qm] }
        })" :width='"7rem"' :height='"1.2rem"'></SelectorGroup>
        <div v-if="ui_state.result_mode == ResultMode.MINI" class="results_instance_container">
            <ResultMinitatures :diff="diff" :store="store" :query_string="query_string"></ResultMinitatures>
        </div>
        <div v-else class="results_instance_container">
            <ResultPlot :store="store" :query_string="query_string" :diff="diff"></ResultPlot>
        </div>
    </div>
</template>
<script setup lang="ts">
import { ref, watch, reactive } from 'vue'
import { SubjectNode, Link, SubQueryType } from '@/utils/sparql/representation';
import { PropertiesOpenEvent, QueryMapper, ResultList } from '@/utils/sparql/querymapper';
import { Vector2, type Vector2Like } from 'three';
import Loading from '../ui/Loading.vue';
import Result from './results/Miniature.vue';
import ResultPlot from './results/Plot.vue';
import OnsetBtn from '../ui/OnsetBtn.vue';
import type { NodeLinkRepository } from '@/utils/sparql/store';
import SelectorGroup from '../ui/SelectorGroup.vue';
import type { NodeLinkRepositoryDiff } from '@/utils/sparql/diff';
import ResultMinitatures from './results/MinitatureList.vue';
enum ResultMode {
    MINI = 'Miniatures',
    PROP = 'Properties',
}
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
const ui_state = reactive({
    result_mode: ResultMode.MINI
})
watch(() => query_string, () => {
    if (!store) {
        return
    }
    let query_props = store.nodes.flatMap(n => n.subqueries.filter(sq => sq.constraint_type == SubQueryType.QUERY_PROP))
    if (query_props.length > 0) {
        ui_state.result_mode = ResultMode.PROP
    } else {
        ui_state.result_mode = ResultMode.MINI
    }
}, { deep: true })
</script>
<style lang="scss">
.results_view {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: start;
    height: 95%;
    width: 30%;
    border-left: 1px solid rgb(192, 213, 191);
}

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


.result_instance_header {
    font-size: 1.5rem;
    font-weight: bold;
    padding: 5px;
    border-bottom: 1px solid rgb(192, 213, 191);
    width: 100%;
    margin-bottom: 12px;
}

</style>
