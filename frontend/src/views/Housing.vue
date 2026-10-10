<template>
  <div class="fade-in">
    <div class="intro"><div><div class="eyebrow">LOCAL HOUSING / TRANSACTIONS</div><h1>价格之外，看看真实成交</h1><p class="subtitle">各地住建部门发布的网签套数与面积，按原始统计范围展示。月度和年度分别读取，缺失数据保留为空。</p></div><RouterLink to="/sources" class="source-link">查看接入范围 ↗</RouterLink></div>
    <div v-if="error" class="error" role="alert">{{ error }}<button @click="load">重试</button></div>
    <section class="panel">
      <div class="panel-head"><div><h2>{{ city }}住宅成交</h2><p class="note">{{ frequency === 'month' ? '月度网签' : '年度统计' }} · {{ countPeriods }} 个期间有数据</p></div><button v-if="items.length" @click="exportData">导出成交数据 ↓</button></div>
      <div class="controls"><label class="small muted">城市 <select v-model="city" aria-label="成交统计城市"><option v-for="c in cities" :key="c.city">{{ c.city }}</option></select></label><div class="segmented" aria-label="成交统计频率"><button :class="{selected:frequency === 'month'}" :aria-pressed="frequency === 'month'" @click="frequency = 'month'">月度</button><button :class="{selected:frequency === 'year'}" :aria-pressed="frequency === 'year'" @click="frequency = 'year'">年度</button></div><div class="segmented" aria-label="成交统计指标"><button :class="{selected:metric === 'transaction_count'}" :aria-pressed="metric === 'transaction_count'" @click="metric = 'transaction_count'">成交套数</button><button :class="{selected:metric === 'area_sqm'}" :aria-pressed="metric === 'area_sqm'" @click="metric = 'area_sqm'">成交面积</button></div></div>
      <p v-if="loading" class="loading" role="status">正在读取住建成交数据…</p>
      <template v-else-if="items.length"><TrendChart :series="series" :unit="metric === 'transaction_count' ? '套' : '㎡'" :description="`${city}${frequency === 'month' ? '月度' : '年度'}住宅成交折线图`"/><div class="notice"><strong>统计范围：</strong>{{ scopes.join('；') }}。<span v-for="note in notes" :key="note">{{ note }} </span></div></template>
      <div v-else-if="!loading && !error" class="empty"><h3>{{ city }}的{{ frequency === 'month' ? '月度' : '年度' }}成交数据尚未取得</h3><p>地方公开方式和统计口径不同，未取得的数据不推算、不填零。</p><p><RouterLink to="/">查看已接入的国家统计局价格趋势 →</RouterLink></p></div>
    </section>
    <section v-if="items.length" class="panel"><div class="panel-head"><div><h2>原始成交观测</h2><p class="note">面积统一为平方米。年度原表若采用万套、万平方米，已按单位换算；不是由每日快照累计得出。</p></div><span class="badge live">住建部门官方数据</span></div><div class="table-wrap"><table><thead><tr><th>期间</th><th>住宅类型</th><th>套数</th><th>面积（㎡）</th><th>官方来源</th></tr></thead><tbody><tr v-for="row in [...items].reverse()" :key="`${row.period}-${row.house_type}-${row.scope}`"><td class="mono">{{ row.period }}</td><td>{{ row.house_type === 'new' ? '新建住宅' : '二手住宅' }}</td><td class="mono">{{ number(row.transaction_count) }}</td><td class="mono">{{ number(row.area_sqm) }}</td><td><a :href="row.source.url" target="_blank" rel="noopener noreferrer">{{ sourceNames[row.source.provider] || row.source.provider }} ↗</a><span class="muted"> · </span><a :href="row.source.snapshot_url">原始快照 ↓</a></td></tr></tbody></table></div></section>
    <p class="note">住建成交统计与国家统计局价格指数属于不同数据集，地理范围也可能不同，不能直接组合计算城市平均售价。</p>
  </div>
</template>

<script setup>
import { computed, onMounted, ref, watch } from 'vue'
import api, { errorMessage } from '../api'
import TrendChart from '../components/TrendChart.vue'
import { downloadCsv } from '../utils'
const cities = ref([]), city = ref('石家庄'), frequency = ref('month'), metric = ref('transaction_count'), items = ref([]), loading = ref(true), error = ref('')
const sourceNames = { beijing: '北京市住建委', shijiazhuang: '石家庄市住建局' }
const number = n => n == null ? '—' : n.toLocaleString('zh-CN', { maximumFractionDigits: 2 })
const countPeriods = computed(() => new Set(items.value.map(r => r.period)).size)
const scopes = computed(() => [...new Set(items.value.map(r => r.scope))])
const notes = computed(() => [...new Set(items.value.map(r => r.note).filter(Boolean))])
const series = computed(() => {
  const periods = []; const keys = [...new Set(items.value.map(r => `${r.house_type}|${r.scope}`))]
  items.value.forEach(r => { if (!periods.includes(r.period)) periods.push(r.period) })
  periods.sort()
  if (frequency.value === 'month' && periods.length) { const first = periods[0], last = periods[periods.length - 1]; let [y,m] = first.split('-').map(Number); while (`${y}-${String(m).padStart(2,'0')}` <= last) { const p = `${y}-${String(m).padStart(2,'0')}`; if (!periods.includes(p)) periods.push(p); m++; if (m === 13) { y++; m = 1 } } periods.sort() }
  return keys.map(key => { const [kind,scope] = key.split('|'); return { city: `${kind === 'new' ? '新建住宅' : '二手住宅'}${scopes.value.length > 1 ? ' · '+scope : ''}`, points: periods.map(period => ({ period, value: items.value.find(r => r.period === period && r.house_type === kind && r.scope === scope)?.[metric.value] ?? null })) } })
})
let requestId = 0
async function load() { const id = ++requestId; loading.value = true; error.value = ''; try { const { data } = await api.get('/housing', { params: { city: city.value, frequency: frequency.value } }); if (id === requestId) items.value = data.items } catch(e) { if (id === requestId) { items.value = []; error.value = errorMessage(e) } } finally { if (id === requestId) loading.value = false } }
function exportData() { downloadCsv(`${city.value}-${frequency.value}-官方成交.csv`, ['城市','期间','频率','住宅类型','成交套数','成交面积(平方米)','统计范围','口径说明','来源链接','网页SHA256'], items.value.map(r => [city.value,r.period,frequency.value,r.house_type === 'new' ? '新建住宅' : '二手住宅',r.transaction_count,r.area_sqm,r.scope,r.note,r.source.url,r.source.sha256])) }
watch([city, frequency], load)
onMounted(async () => { try { cities.value = (await api.get('/cities')).data.cities } catch(e) { error.value = errorMessage(e) }; await load() })
</script>
