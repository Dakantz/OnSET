<template>

    <div id="threed_minimap">
        <Loading v-if="ui_state.loading"></Loading>
        <div id="threed_graph"></div>
    </div>
</template>
<script setup lang="ts">
import { Api } from '@/api/client.ts/Api';
import { BACKEND_URL } from '@/utils/config';
import type { Link } from '@/utils/sparql/representation';
import type { NodeLinkRepository } from '@/utils/sparql/store';
import type { SubjectInCircle } from '@/utils/three-man/CircleMan3D';
import { OverviewCircles } from '@/utils/three-man/OverviewCircles';
import { onMounted, reactive, watch } from 'vue';
import Loading from '@/components/ui/Loading.vue';


const api = new Api({
    baseURL: BACKEND_URL
})
const { store, query_string, hoveredLink } = defineProps({
    store: {
        type: Object as () => NodeLinkRepository,
        required: true
    },
    query_string: {
        type: String,
        required: true
    },
    hoveredLink: {
        type: Object as () => Link | null,
        required: true
    }
})
const ui_state = reactive({
    loading: false,
})
const overviewBox = new OverviewCircles('#threed_graph')

watch(() => query_string, (new_val) => {
    if (overviewBox.nodes.length == 0 && overviewBox.renderer) {
        return
    }

    overviewBox.updateLinks(store)
}, { deep: false })

onMounted(() => {
    // circleman.clicked_node = (node: NodeType) => {
    //     console.log('clicked_node', node)
    //     api.classes.getLinksClassesLinksGet({
    //         subject_id: node.subject_id
    //     }).then(resp => {
    //         console.log('resp', resp)
    //         circleman.removeLinks()
    //         const links = resp.data
    //         for (const out of links.targets) {
    //             circleman.addLink(links.source.subject_id, out.target.subject_id, out.count)
    //         }
    //     }).catch(console.error)
    // }

    (async () => {
        ui_state.loading = true
        const resp_classes = await api.classes.getFullClassesClassesFullGet()
        ui_state.loading = false
        overviewBox.nodes = resp_classes.data as SubjectInCircle[]
        // overviewBox.dimensions.width = 1000
        overviewBox.initPackedCircles()
        if (store && store.nodes.length > 0) {
            overviewBox.updateLinks(store)
        }
    })().catch((e) => {
        console.error(e)
        ui_state.loading = false
    })

})

watch(() => hoveredLink, (new_val) => {
    previewLink(new_val)
}, { deep: false })
const previewLink = (l: Link | null) => {
    // console.log('Preview link', l)
    if (l) {
        overviewBox.previewLink(l)
    } else {
        overviewBox.hidePreview()
    }
}
</script>

<style lang="scss">
#threed_graph {
    width: 100%;
    height: 100%;
}

#threed_minimap {
    aspect-ratio: 1;
    height: 15vw;
    width: 15vw;
    position: relative;
    left: calc(100% - 15vw - 20px);
    bottom: calc(15vw + 20px);
    // translate: calc(100%) calc(80%);
    z-index: 20;
    background-color: #ffffff;
    border: 1px solid #8fa88f;
    padding: 4px;
    margin: 5px;
}
</style>