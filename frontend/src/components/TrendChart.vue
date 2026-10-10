<template><div ref="root" class="chart" role="img" :aria-label="description" /></template>

<script setup>
import { onMounted, onUnmounted, ref, watch } from 'vue'
import { use, init } from 'echarts/core'
import { LineChart } from 'echarts/charts'
import { GridComponent, TooltipComponent, LegendComponent, DataZoomComponent, MarkLineComponent } from 'echarts/components'
import { CanvasRenderer } from 'echarts/renderers'

use([LineChart, GridComponent, TooltipComponent, LegendComponent, DataZoomComponent, MarkLineComponent, CanvasRenderer])
const props = defineProps({ series: { type: Array, default: () => [] }, unit: { type: String, default: '%' }, baseline: { type: Number, default: 0 }, description: { type: String, default: '城市官方数据折线图' } })
const colors = ['#3959cf', '#138578', '#bd65a1', '#df9550', '#708aab', '#6c58ad', '#bd6464', '#528f93']
const root = ref(null)
let chart, observer
function render() {
  if (!chart) return
  const dates = [...new Set(props.series.flatMap(s => s.points.map(p => p.period)))].sort()
  chart.setOption({
    animation: !window.matchMedia('(prefers-reduced-motion: reduce)').matches,
    color: colors,
    textStyle: { fontFamily: 'PingFang SC, sans-serif' },
    legend: { bottom: 0, icon: 'roundRect', itemWidth: 16, itemHeight: 3, textStyle: { color: '#62748c', fontSize: 12 } },
    tooltip: { trigger: 'axis', confine: true, valueFormatter: v => v == null ? '未发布' : Number(v).toFixed(2) + (props.unit === '%' ? '%' : ''), backgroundColor: '#fff', borderColor: '#dde5f0', textStyle: { color: '#142b47' } },
    grid: { left: 58, right: 26, top: 35, bottom: 82 },
    xAxis: { type: 'category', boundaryGap: false, data: dates, axisLine: { lineStyle: { color: '#dde5f0' } }, axisTick: { show: false }, axisLabel: { color: '#62748c', fontSize: 11, hideOverlap: true } },
    yAxis: { type: 'value', scale: true, name: props.unit, nameTextStyle: { color: '#62748c' }, axisLabel: { color: '#62748c', fontSize: 11 }, splitLine: { lineStyle: { color: '#edf1f7' } } },
    dataZoom: [{ type: 'inside', filterMode: 'none' }, { type: 'slider', bottom: 29, height: 18, borderColor: '#dde5f0', backgroundColor: '#f8fafe', fillerColor: '#3959cf18', showDetail: false }],
    series: props.series.map((s, i) => ({ name: s.city, type: 'line', showSymbol: s.points.filter(p => p.value !== null).length === 1, symbolSize: 7, smooth: false, connectNulls: false, lineStyle: { width: 2.3 }, data: dates.map(d => s.points.find(p => p.period === d)?.value ?? null),
      markLine: i === 0 && props.unit !== '套' && props.unit !== '㎡' ? { silent: true, symbol: 'none', label: { show: false }, lineStyle: { color: '#9bacc1', type: 'dashed', width: 1 }, data: [{ yAxis: props.baseline }] } : undefined }))
  }, { notMerge: true })
}
watch(() => [props.series, props.unit, props.baseline], render, { deep: true })
onMounted(() => { chart = init(root.value); observer = new ResizeObserver(() => chart?.resize()); observer.observe(root.value); render() })
onUnmounted(() => { observer?.disconnect(); chart?.dispose(); chart = null })
</script>
