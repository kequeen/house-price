<template>
  <div class="fade-in">
    <div class="intro">
      <div><div class="eyebrow">CITY HOUSING / PRICE MONITOR</div><h1>把城市放在同一条时间线上</h1><p class="subtitle">追踪一、二线城市的住宅价格变化。新房与二手房分别观察，数据直接来自国家统计局月度公告。</p></div>
      <div class="issue"><small>最新数据月份</small><strong>{{ overview.latest_period || '待同步' }}</strong></div>
    </div>
    <div v-if="error" class="error" role="alert">{{ error }}<button @click="loadAll">重试</button></div>
    <p v-if="loading" class="loading" role="status">正在读取官方数据…</p>
    <dl class="stats-strip">
      <div class="stat"><dt>一、二线城市覆盖</dt><dd>{{ overview.covered_city_count ?? '—' }}<small>/ 35 城</small></dd></div>
      <div class="stat"><dt>一线 / 二线</dt><dd>{{ overview.first_tier_count ?? '—' }}<small>/ {{ overview.second_tier_count ?? '—' }} 城</small></dd></div>
      <div class="stat"><dt>已收录月度公告</dt><dd>{{ overview.month_count ?? '—' }}<small>个月</small></dd></div>
      <div class="stat"><dt>一、二线价格观测</dt><dd>{{ formatCount(overview.price_record_count) }}<small>条</small></dd></div>
    </dl>
    <div v-if="!loading && !overview.latest_period && !error" class="panel empty"><h3>先同步一组官方数据</h3><p>选择起始月份，系统会读取国家统计局公告并保留来源。</p><RouterLink to="/sources">前往数据来源 →</RouterLink></div>
    <section v-if="overview.latest_period" class="panel" aria-labelledby="compare-title">
      <div class="panel-head"><div><h2 id="compare-title">城市价格对比</h2><p class="note">选择下方城市加入对比，最多 8 城。当前 {{ selectedCities.length }} 城。</p></div><button @click="exportData">导出官方原始指数 ↓</button></div>
      <div class="controls">
        <div class="segmented" aria-label="住宅类型"><button v-for="(label, key) in houseTypes" :key="key" :class="{ selected: houseType === key }" :aria-pressed="houseType === key" @click="houseType = key">{{ label }}</button></div>
        <div class="segmented" aria-label="价格指标"><button v-for="(label, key) in metrics" :key="key" :class="{ selected: metric === key }" :aria-pressed="metric === key" @click="metric = key">{{ label }}</button></div>
        <div class="date-range"><label for="start-month">从</label><input id="start-month" type="month" v-model="start" :min="overview.first_period" :max="end"><label for="end-month">至</label><input id="end-month" type="month" v-model="end" :min="start" :max="overview.latest_period"></div>
      </div>
      <div class="chart-toolbar"><div class="selected-chips"><button v-for="city in selectedCities" :key="city" @click="toggleCity(city)" :aria-label="'移除'+city">{{ city }}<span>×</span></button></div><small class="muted">{{ metrics[metric] }} · {{ houseTypes[houseType] }} <span v-if="chartLoading"> / 加载中</span></small></div>
      <TrendChart :series="chartData.series || []" :unit="chartData.unit || '%'" :baseline="metric === 'relative_index' ? 100 : 0" :description="`${selectedCities.join('、')}${houseTypes[houseType]}${metrics[metric]}折线图`" />
      <p class="note">{{ chartData.methodology }} <span v-if="metric === 'relative_index'">基准月：{{ start }}。</span>缺失月份显示断点；价格指数不表示每平方米售价。</p>
    </section>
    <section v-if="overview.latest_period" aria-labelledby="all-cities-title" class="city-section">
      <div class="panel-head"><div><h2 id="all-cities-title">35 城，一眼看见各自走势</h2><p class="note">{{ houseTypes[houseType] }} · 最近 24 个月同比曲线 · 点击城市加入上方对比。卡片纵轴分别缩放，幅度以数值为准。</p></div><div class="city-filters"><input v-model="search" placeholder="搜索城市" aria-label="搜索城市"><select v-model="tier" aria-label="城市级别"><option value="all">全部城市</option><option value="1">一线城市</option><option value="2">二线城市</option></select></div></div>
      <p v-if="selectionMessage" class="notice" role="status">{{ selectionMessage }}</p>
      <div class="city-grid"><button v-for="city in filteredCities" :key="city.city" class="city-card" :class="{ chosen: selectedCities.includes(city.city) }" :aria-pressed="selectedCities.includes(city.city)" @click="toggleCity(city.city)">
        <div class="city-card-top"><strong>{{ city.city }}</strong><span class="city-tier">{{ city.tier === 1 ? '一线' : city.province }}</span><span class="check">{{ selectedCities.includes(city.city) ? '✓' : '+' }}</span></div>
        <div class="city-number" :class="signClass(city[houseType].yoy_change)">{{ percent(city[houseType].yoy_change) }}<small>同比</small></div>
        <Sparkline :points="city[houseType].sparkline" :label="`${city.city}最近24个月${houseTypes[houseType]}同比变化`" :color="city[houseType].yoy_change > 0 ? '#d15c57' : '#138578'" />
        <div class="city-card-bottom"><span>环比 <b :class="signClass(city[houseType].mom_change)">{{ percent(city[houseType].mom_change) }}</b></span><span>{{ city[houseType].period || '未取得' }}</span></div>
      </button></div>
      <div v-if="!filteredCities.length" class="empty">没有匹配的城市，请调整搜索或城市级别。</div>
    </section>
    <section v-if="overview.latest_period" class="panel" aria-labelledby="detail-title">
      <div class="panel-head"><div><h2 id="detail-title">月度数据与官方出处</h2><p class="note">{{ houseTypes[houseType] }}，当前展示全部 35 城在所选月份的数据。环比、同比变化均为官方指数减 100。</p></div><select v-model="detailPeriod" aria-label="原始数据月份"><option v-for="period in [...(overview.periods || [])].reverse()" :key="period">{{ period }}</option></select></div>
      <div class="table-wrap"><table><thead><tr><th>城市</th><th>级别</th><th>环比变化</th><th>同比变化</th><th>官方环比指数</th><th>官方同比指数</th><th>出处</th></tr></thead><tbody><tr v-for="row in observations" :key="row.city"><td><strong>{{ row.city }}</strong></td><td class="muted">{{ row.tier === 1 ? '一线' : '二线' }}</td><td class="mono" :class="signClass(row.mom_change)">{{ percent(row.mom_change) }}</td><td class="mono" :class="signClass(row.yoy_change)">{{ percent(row.yoy_change) }}</td><td class="mono">{{ row.mom_index ?? '—' }}</td><td class="mono">{{ row.yoy_index ?? '—' }}</td><td><a :href="row.source.url" target="_blank" rel="noopener noreferrer">国家统计局 ↗</a><span class="muted small"> · </span><a :href="row.source.snapshot_url">原始快照 ↓</a></td></tr></tbody></table></div>
      <div v-if="!observations.length" class="empty">该月尚未取得数据。</div>
    </section>
    <details class="panel"><summary>如何理解这些曲线，以及城市级别的定义</summary><p class="note">同比变化比较上年同月，环比变化比较上月。例如环比指数 99.5 表示环比下降 0.5%。相对指数将起始月设为 100，之后逐月连乘环比，帮助比较累计变化；它是本项目计算的序列，不能作为官方定基指数。官方环比有取整误差，跨基期也应结合统计制度调整阅读。</p><p class="note">一、二线沿用国家统计局 70 城统计分类，共 4 个一线和 31 个二线城市。苏州、东莞等城市不属于这份样本，并不代表它们的经济地位较低。<a :href="overview.tier_source_url" target="_blank" rel="noopener noreferrer">查看官方分类 ↗</a></p></details>
  </div>
</template>

<script setup>
import { computed, onMounted, ref, watch } from 'vue'
import api, { errorMessage } from '../api'
import TrendChart from '../components/TrendChart.vue'
import Sparkline from '../components/Sparkline.vue'
const overview = ref({}), cities = ref([]), observations = ref([]), chartData = ref({}), error = ref(''), loading = ref(true), chartLoading = ref(false)
const houseType = ref('second_hand'), metric = ref('yoy_change'), selectedCities = ref(['北京', '上海', '广州', '深圳']), start = ref(''), end = ref(''), detailPeriod = ref(''), search = ref(''), tier = ref('all'), selectionMessage = ref('')
const houseTypes = { new: '新建商品住宅', second_hand: '二手住宅' }, metrics = { yoy_change: '同比变化', mom_change: '环比变化', relative_index: '相对指数' }
const filteredCities = computed(() => cities.value.filter(c => c.city.includes(search.value.trim()) && (tier.value === 'all' || String(c.tier) === tier.value)))
const percent = value => value == null ? '—' : `${value > 0 ? '+' : ''}${value.toFixed(1)}%`
const signClass = value => value == null || value === 0 ? 'neutral' : value > 0 ? 'positive' : 'negative'
const formatCount = value => value == null ? '—' : value.toLocaleString('zh-CN')
function toggleCity(city) {
  selectionMessage.value = ''
  if (selectedCities.value.includes(city)) { if (selectedCities.value.length === 1) { selectionMessage.value = '至少保留一个城市用于对比。'; return } selectedCities.value = selectedCities.value.filter(c => c !== city) }
  else { if (selectedCities.value.length === 8) { selectionMessage.value = '最多比较 8 个城市，请先移除一个城市。'; return } selectedCities.value = [...selectedCities.value, city] }
}
let chartRequest = 0, tableRequest = 0
async function loadChart() {
  if (!start.value || !end.value) return
  const request = ++chartRequest; chartLoading.value = true
  try { const { data } = await api.get('/series', { params: { cities: selectedCities.value.join(','), house_type: houseType.value, metric: metric.value, start: start.value, end: end.value } }); if (request === chartRequest) chartData.value = data }
  catch (e) { if (request === chartRequest) { chartData.value = {}; error.value = errorMessage(e) } }
  finally { if (request === chartRequest) chartLoading.value = false }
}
async function loadObservations() {
  if (!detailPeriod.value) return
  const request = ++tableRequest
  try { const { data } = await api.get('/observations', { params: { period: detailPeriod.value, house_type: houseType.value } }); if (request === tableRequest) observations.value = data.items }
  catch (e) { if (request === tableRequest) { observations.value = []; error.value = errorMessage(e) } }
}
async function loadAll() {
  loading.value = true; error.value = ''
  try { const [summary, catalog] = await Promise.all([api.get('/overview'), api.get('/cities')]); overview.value = summary.data; cities.value = catalog.data.cities; start.value ||= summary.data.first_period || ''; end.value ||= summary.data.latest_period || ''; detailPeriod.value ||= summary.data.latest_period || ''; await Promise.all([loadChart(), loadObservations()]) }
  catch (e) { error.value = errorMessage(e) }
  finally { loading.value = false }
}
function exportData() { const params = new URLSearchParams({ cities: selectedCities.value.join(','), house_type: houseType.value, start: start.value, end: end.value }); window.location.assign(`/api/export/prices?${params}`) }
watch([selectedCities, houseType, metric, start, end], loadChart)
watch([detailPeriod, houseType], loadObservations)
onMounted(loadAll)
</script>

<style scoped>
.selected-chips{display:flex;gap:7px;flex-wrap:wrap}.selected-chips button{padding:4px 10px;background:var(--tint);border-color:#dce2fb;color:var(--blue);font-size:12px}.selected-chips span{margin-left:10px;color:#8190c0}.city-section{margin:32px 0}.city-filters{display:flex;gap:8px}.city-filters input{width:145px;font-size:12px}.city-filters select{font-size:12px}.city-grid{display:grid;grid-template-columns:repeat(5,minmax(0,1fr));gap:12px}.city-card{text-align:left;background:#fff;padding:16px 17px;border-radius:11px;transition:border-color .2s,box-shadow .2s}.city-card:hover{border-color:#8297df;box-shadow:0 4px 16px #233b6510}.city-card.chosen{border-color:var(--blue);box-shadow:inset 0 0 0 1px #3959cf22}.city-card-top{display:flex;align-items:center;gap:8px}.city-card-top strong{font-size:15px}.city-tier{font-size:10px;color:var(--muted)}.check{margin-left:auto;width:18px;height:18px;text-align:center;line-height:18px;font-size:12px;border-radius:50%;background:var(--paper);color:var(--muted)}.chosen .check{background:var(--blue);color:white}.city-number{font-family:"Avenir Next",monospace;font-size:24px;font-weight:550;margin:7px 0 6px}.city-number small{font-family:"PingFang SC",sans-serif;font-size:10px;font-weight:400;color:var(--muted);margin-left:7px}.city-card-bottom{display:flex;justify-content:space-between;font-size:10px;color:var(--muted);margin-top:9px}.city-card-bottom b{font-weight:500}@media(max-width:1100px){.city-grid{grid-template-columns:repeat(4,minmax(0,1fr))}}@media(max-width:850px){.city-grid{grid-template-columns:repeat(3,minmax(0,1fr))}}@media(max-width:600px){.city-grid{grid-template-columns:repeat(2,minmax(0,1fr));gap:9px}.city-card{padding:13px}.city-card-top{gap:5px}.city-tier{font-size:9px}.city-filters{width:100%}.city-filters input{flex:1}}
</style>
