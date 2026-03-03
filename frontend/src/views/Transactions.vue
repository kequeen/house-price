<template>
  <div class="transactions">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>成交记录查询</span>
        </div>
      </template>
      
      <el-form :inline="true" :model="filters" class="filter-form">
        <el-form-item label="区域">
          <el-select v-model="filters.region" placeholder="选择区域" clearable @change="onRegionChange">
            <el-option v-for="r in regions" :key="r" :label="r" :value="r" />
          </el-select>
        </el-form-item>
        <el-form-item label="片区">
          <el-select v-model="filters.district" placeholder="选择片区" clearable>
            <el-option v-for="d in districts" :key="d" :label="d" :value="d" />
          </el-select>
        </el-form-item>
        <el-form-item label="年份">
          <el-select v-model="filters.year" placeholder="选择年份" clearable>
            <el-option v-for="y in years" :key="y" :label="y" :value="y" />
          </el-select>
        </el-form-item>
        <el-form-item label="数据来源">
          <el-select v-model="filters.data_source" placeholder="选择来源" clearable>
            <el-option label="链家" value="lianjia" />
            <el-option label="房管局" value="government" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="loadData">查询</el-button>
          <el-button @click="resetFilters">重置</el-button>
        </el-form-item>
      </el-form>
      
      <el-table :data="transactions" style="width: 100%" v-loading="loading">
        <el-table-column prop="region" label="区域" width="100" />
        <el-table-column prop="district" label="片区" width="100" />
        <el-table-column prop="community" label="小区" min-width="150" />
        <el-table-column prop="transaction_date" label="成交日期" width="120">
          <template #default="{ row }">
            {{ formatDate(row.transaction_date) }}
          </template>
        </el-table-column>
        <el-table-column prop="price" label="总价(万)" width="100">
          <template #default="{ row }">
            {{ row.price ? row.price.toFixed(0) : '-' }}
          </template>
        </el-table-column>
        <el-table-column prop="unit_price" label="单价(元/㎡)" width="120">
          <template #default="{ row }">
            {{ row.unit_price ? row.unit_price.toFixed(0) : '-' }}
          </template>
        </el-table-column>
        <el-table-column prop="area" label="面积(㎡)" width="100">
          <template #default="{ row }">
            {{ row.area ? row.area.toFixed(2) : '-' }}
          </template>
        </el-table-column>
        <el-table-column prop="bedrooms" label="户型" width="80">
          <template #default="{ row }">
            {{ row.bedrooms }}室{{ row.living_rooms }}厅
          </template>
        </el-table-column>
        <el-table-column prop="data_source" label="来源" width="100">
          <template #default="{ row }">
            <el-tag :type="row.data_source === 'lianjia' ? 'primary' : 'success'" size="small">
              {{ row.data_source === 'lianjia' ? '链家' : '房管局' }}
            </el-tag>
          </template>
        </el-table-column>
      </el-table>
      
      <el-pagination
        v-model:current-page="pagination.page"
        v-model:page-size="pagination.pageSize"
        :page-sizes="[10, 20, 50, 100]"
        :total="pagination.total"
        layout="total, sizes, prev, pager, next, jumper"
        @size-change="loadData"
        @current-change="loadData"
        style="margin-top: 20px; justify-content: flex-end;"
      />
    </el-card>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { transactionApi } from '../api'

const loading = ref(false)
const transactions = ref([])
const regions = ref([])
const districts = ref([])
const years = ref([])

const filters = reactive({
  region: '',
  district: '',
  year: null,
  data_source: ''
})

const pagination = reactive({
  page: 1,
  pageSize: 20,
  total: 0
})

const formatDate = (date) => {
  if (!date) return '-'
  return new Date(date).toLocaleDateString('zh-CN')
}

const loadRegions = async () => {
  try {
    const { data } = await transactionApi.getRegions()
    regions.value = data?.regions || []
  } catch (e) {
    console.error('加载区域失败', e)
  }
}

const loadDistricts = async (region) => {
  if (!region) {
    districts.value = []
    return
  }
  try {
    const { data } = await transactionApi.getDistricts(region)
    districts.value = data?.districts || []
  } catch (e) {
    console.error('加载片区失败', e)
  }
}

const loadYears = async () => {
  try {
    const { data } = await transactionApi.getYears()
    years.value = data?.years || []
  } catch (e) {
    console.error('加载年份失败', e)
  }
}

const loadData = async () => {
  loading.value = true
  try {
    const params = {
      page: pagination.page,
      page_size: pagination.pageSize
    }
    
    if (filters.region) params.region = filters.region
    if (filters.district) params.district = filters.district
    if (filters.year) params.year = filters.year
    if (filters.data_source) params.data_source = filters.data_source
    
    const { data } = await transactionApi.getList(params)
    transactions.value = data?.items || []
    pagination.total = data?.total || 0
  } catch (e) {
    console.error('加载数据失败', e)
  } finally {
    loading.value = false
  }
}

const onRegionChange = (region) => {
  filters.district = ''
  loadDistricts(region)
}

const resetFilters = () => {
  filters.region = ''
  filters.district = ''
  filters.year = null
  filters.data_source = ''
  districts.value = []
  pagination.page = 1
  loadData()
}

onMounted(async () => {
  await Promise.all([loadRegions(), loadYears()])
  await loadData()
})
</script>

<style scoped>
.filter-form {
  margin-bottom: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
</style>
