<template>
  <svg viewBox="0 0 180 46" class="sparkline" role="img" :aria-label="label" preserveAspectRatio="none">
    <line x1="0" :y1="zero" x2="180" :y2="zero" stroke="#dde5f0" stroke-dasharray="3 4" />
    <path v-for="(path, index) in paths" :key="index" :d="path" fill="none" :stroke="color" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" />
  </svg>
</template>

<script setup>
import { computed } from 'vue'
const props = defineProps({ points: { type: Array, default: () => [] }, label: { type: String, default: '最近24个月同比变化' }, color: { type: String, default: '#3959cf' } })
const extent = computed(() => { const values = props.points.map(p => p.value).filter(v => v !== null); return { min: Math.min(0, ...values), max: Math.max(0, ...values) } })
const y = value => 40 - (value - extent.value.min) / (extent.value.max - extent.value.min || 1) * 34
const zero = computed(() => y(0))
const paths = computed(() => {
  const result = []; let current = ''
  props.points.forEach((p, i) => { if (p.value === null) { if (current) result.push(current); current = ''; return } const x = i / Math.max(1, props.points.length - 1) * 180; current += `${current ? 'L' : 'M'}${x.toFixed(1)},${y(p.value).toFixed(1)} ` })
  if (current) result.push(current)
  return result
})
</script>

<style scoped>.sparkline{width:100%;height:46px;display:block}</style>
