<template>
  <div class="fade-in">
    <div class="intro"><div><div class="eyebrow">DATA SOURCES / TRACEABILITY</div><h1>每条曲线，都有出处</h1><p class="subtitle">查看官方渠道的覆盖范围、原始公告和同步记录。只有通过表格校验的数据才进入图表。</p></div><span class="badge live">来源链接与原始快照</span></div>
    <div v-if="error" class="error" role="alert">{{ error }}<button @click="loadAll">重试</button></div>
    <section class="panel"><div class="panel-head"><div><h2>官方数据渠道</h2><p class="note">“已接入”表示已取得可核验观测；尚未接入的地方渠道保留说明。</p></div></div><div class="table-wrap"><table><thead><tr><th>数据源</th><th>城市范围</th><th>接入状态</th><th>数据期间</th><th>观测数</th><th>官方入口</th></tr></thead><tbody><tr v-for="source in sources" :key="source.key"><td><strong>{{ source.name }}</strong></td><td>{{ source.city }}</td><td><span class="badge" :class="source.status === 'connected' ? 'live' : 'wait'">{{ statusLabel[source.status] }}</span></td><td class="mono">{{ source.first_period ? source.first_period + ' — ' + source.latest_period : '—' }}</td><td class="mono">{{ source.record_count.toLocaleString() }}</td><td><a :href="source.url" target="_blank" rel="noopener noreferrer">访问官网 ↗</a></td></tr></tbody></table></div><div class="source-notes"><p v-for="source in sources" :key="source.key" class="note"><strong>{{ source.name }}：</strong>{{ source.note }}</p></div></section>
    <section class="panel"><div class="panel-head"><div><h2>同步官方数据</h2><p class="note">按月查找公告并校验完整性。重复同步不会增加重复观测，失败时保留已有数据。</p></div><span v-if="activeRun" class="badge wait">同步中</span></div>
      <form @submit.prevent="startSync" class="form-row"><label>起始月份<input type="month" v-model="start" min="2011-01" :max="end" required :disabled="!!activeRun"></label><label>结束月份<input type="month" v-model="end" :min="start" :max="latestCompleted" required :disabled="!!activeRun"></label><label class="checkbox-label"><input type="checkbox" v-model="includeHousing" :disabled="!!activeRun">同时获取已接入住建成交</label><label class="checkbox-label"><input type="checkbox" v-model="refresh" :disabled="!!activeRun">重新读取原网页</label><button type="submit" class="primary" :disabled="submitting || !!activeRun">{{ submitting ? '提交中…' : activeRun ? '正在同步…' : '开始同步' }}</button></form>
      <p class="note table-note">结束月份尚无公告时，保持未取得状态。单次最多 61 个月，更长历史可分批同步。重新读取原网页用于核查官方修订，会保留前后快照。</p>
      <div v-if="activeRun" class="notice table-note" role="status">{{ activeRun.progress }}<br><span class="small">已更新 {{ activeRun.price_records }} 条价格指数、{{ activeRun.housing_records }} 条成交观测。</span></div>
    </section>
    <section class="panel"><div class="panel-head"><div><h2>同步记录</h2><p class="note">每次任务保存进度和具体失败月份；“部分完成”表示至少有一个渠道或月份未取得。</p></div><button @click="loadSources">刷新状态</button></div>
      <div v-if="!runs.length" class="empty">尚无同步记录。</div><article v-for="run in runs" :key="run.id" class="run"><div class="run-top"><strong>{{ run.start_period }} — {{ run.end_period }}</strong><span class="badge" :class="run.status === 'succeeded' ? 'live' : 'wait'">{{ runLabels[run.status] || run.status }}</span></div><p class="small">{{ run.progress }}</p><p class="note">{{ formatTime(run.started_at) }} · 新增或更新 {{ run.price_records }} 条价格指数 / {{ run.housing_records }} 条成交统计</p><details v-if="run.errors.length" class="table-note"><summary>查看 {{ run.errors.length }} 条未取得或失败说明</summary><div class="run-errors"><p v-for="(issue,i) in run.errors" :key="i">{{ issue.provider }} {{ issue.period || '' }}：{{ issue.message }}</p></div></details></article>
    </section>
    <section class="panel"><div class="panel-head"><div><h2>公告与原始网页</h2><p class="note">共 {{ documents.total || 0 }} 份来源快照。每份快照保存采集时间、网页校验值和解析版本。</p></div><div class="button-row"><button :disabled="page <= 1" @click="page--">上一页</button><span class="small muted">{{ page }} / {{ Math.max(1,Math.ceil((documents.total || 0)/20)) }}</span><button :disabled="page*20 >= (documents.total || 0)" @click="page++">下一页</button></div></div>
      <div class="table-wrap"><table><thead><tr><th>公告 / 表格</th><th>采集时间</th><th>网页校验值</th><th>查看</th></tr></thead><tbody><tr v-for="doc in documents.items || []" :key="doc.id"><td class="documents-title">{{ doc.title }}</td><td class="small">{{ formatTime(doc.fetched_at) }}</td><td class="mono small" :title="doc.sha256">{{ doc.sha256.slice(0,14) }}…</td><td><a :href="doc.url" target="_blank" rel="noopener noreferrer">原公告 ↗</a><span class="muted"> · </span><a :href="doc.snapshot_url">原始快照 ↓</a></td></tr></tbody></table></div>
    </section>
  </div>
</template>

<script setup>
import { onMounted, onUnmounted, ref, watch } from 'vue'
import api, { errorMessage } from '../api'
const sources = ref([]), runs = ref([]), documents = ref({}), page = ref(1), error = ref(''), activeRun = ref(null), submitting = ref(false)
const today = new Date(), completed = new Date(today.getFullYear(), today.getMonth()-1,1)
const latestCompleted = `${completed.getFullYear()}-${String(completed.getMonth()+1).padStart(2,'0')}`
const start = ref('2023-01'), end = ref(latestCompleted), includeHousing = ref(true), refresh = ref(false)
const statusLabel = { connected: '已接入', ready: '待同步', unavailable: '尚未接入' }, runLabels = { succeeded: '已完成', partial: '部分完成', failed: '失败', running: '运行中' }
const formatTime = value => value ? new Date(value).toLocaleString('zh-CN', { hour12:false }) : '—'
let timer, disposed = false
async function loadSources() { try { const { data } = await api.get('/sources'); sources.value = data.sources; runs.value = data.runs; activeRun.value = data.runs.find(r => r.status === 'running') || null } catch(e) { error.value = errorMessage(e) } }
async function loadDocuments() { try { documents.value = (await api.get('/documents', { params: { page:page.value,page_size:20 } })).data } catch(e) { error.value = errorMessage(e) } }
async function loadAll() { error.value = ''; try { await Promise.all([loadSources(),loadDocuments()]); if(activeRun.value) poll() } catch(e) { error.value = errorMessage(e) } }
async function poll() { clearTimeout(timer); if(!activeRun.value || disposed) return; try { const { data } = await api.get(`/sync/${activeRun.value.id}`); activeRun.value = data.status === 'running' ? data : null; if(!activeRun.value) { await loadAll(); return }; runs.value = [data,...runs.value.filter(r => r.id !== data.id)] } catch(e) { error.value = errorMessage(e) }; if(!disposed) timer = setTimeout(poll,2500) }
async function startSync() { error.value = ''; submitting.value = true; try { const { data } = await api.post('/sync', { start_period:start.value,end_period:end.value,refresh:refresh.value,include_housing:includeHousing.value }); activeRun.value = { ...data,progress:'正在查找官方公告',price_records:0,housing_records:0 }; poll() } catch(e) { error.value = errorMessage(e) } finally { submitting.value = false } }
watch(page, loadDocuments)
onMounted(loadAll)
onUnmounted(() => { disposed = true; clearTimeout(timer) })
</script>

<style scoped>.source-notes{display:grid;gap:9px;margin-top:20px}.source-notes strong{color:var(--ink);font-weight:500}</style>
