<template>
    <div class="draw_panel">
        <canvas class="draw_canvas" ref="canvas" @mousedown="startDrawing" @mouseup="stopDrawing"
            @mouseleave="stopDrawing" @mousemove="draw" :width="draw_state.width" :height="draw_state.height"></canvas>
        <button @click="clearCanvas">Clear</button>
    </div>
</template>

<script setup lang="ts">

import { computed, defineProps, onMounted, reactive, ref, watch } from 'vue'
const image_str = defineModel<string>()
const canvas = ref<HTMLCanvasElement | null>(null)



const draw_state = reactive({
    drawing: false,
    lastX: 0,
    lastY: 0,
    color: '#000000',
    lineWidth: 5,
    width: 128,
    height: 128,
})
const mousepos = (evt: MouseEvent) => {
    const c = canvas.value
    if (c) {
        const rect = c.getBoundingClientRect()
        console.log('mousepos', evt, rect, { x: evt.layerX - rect.left, y: evt.layerY - rect.top })
        let scale = {
            x: c.width / rect.width,
            y: c.height / rect.height
        }
        return {
            x: (evt.clientX - rect.left) * scale.x,
            y: (evt.clientY - rect.top) * scale.y
        }
    }
    return { x: 0, y: 0 }
}
const canvasCtx = computed(() => {
    const c = canvas.value
    if (c) {
        return c.getContext('2d')
    }
    return null
})
const clearCanvas = () => {
    preClearCanvas()
    image_str.value = ""

}
const preClearCanvas = () => {
    const ctx = canvasCtx.value
    const c = canvas.value
    if (ctx && c) {
        ctx.clearRect(0, 0, c.width, c.height)
        ctx.fillStyle = 'white'
        ctx.fillRect(0, 0, c.width, c.height)

    }
}
const startDrawing = (event: MouseEvent) => {
    console.log('startDrawing', event)
    draw_state.drawing = true
    const c = canvas.value
    if (c) {

        const pos = mousepos(event)
        draw_state.lastX = pos.x
        draw_state.lastY = pos.y
    }
}
const stopDrawing = () => {
    draw_state.drawing = false
}
const draw = (event: MouseEvent) => {
    if (!draw_state.drawing) return
    const ctx = canvasCtx.value
    if (ctx) {
        const pos = mousepos(event)
        ctx.strokeStyle = draw_state.color
        ctx.lineWidth = draw_state.lineWidth
        ctx.beginPath()
        ctx.moveTo(draw_state.lastX, draw_state.lastY)
        ctx.lineTo(pos.x, pos.y)
        ctx.stroke()
        draw_state.lastX = pos.x
        draw_state.lastY = pos.y

    }
    const c = canvas.value
    if (!c) return
    image_str.value = c.toDataURL('image/png')

}
const drawImageString = (image_str: string) => {
    const c = canvas.value
    if (!c) return
    const ctx = c.getContext('2d')
    if (!ctx) return
    preClearCanvas()
    if (!image_str) return

    console.log('Loading image from string', image_str)
    const img = new Image()
    img.onload = () => {
        ctx.drawImage(img, 0, 0, c.width, c.height)
    }
    img.src = image_str
}
watch(() => image_str, (new_val) => {
    if (new_val && new_val.value != image_str.value) {
        drawImageString(new_val.value)
    }
})
onMounted(() => {
    preClearCanvas()
    drawImageString(image_str.value)
})

</script>


<style lang="scss" scoped>
.draw_panel {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    width: calc(v-bind("draw_state.width"));
    height: calc(v-bind("draw_state.height"));
}

.draw_canvas {
    width: 100%;
    height: 100%;
    cursor: crosshair;
    border: 1px solid #ccc;
    background-color: #ffffff;
    border: 1px solid #ccc;
}
</style>