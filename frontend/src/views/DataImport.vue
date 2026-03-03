<template>
  <div class="data-import">
    <el-row :gutter="20">
      <el-col :span="12">
        <el-card>
          <template #header>
            <span>导入房管局数据</span>
          </template>
          
          <el-alert
            title="数据格式说明"
            type="info"
            :closable="false"
            style="margin-bottom: 20px;"
          >
            <p>支持 CSV 和 Excel 格式，必需字段：region（区域）</p>
            <p>可选字段：district, community, transaction_date, price, unit_price, area, property_type, floor, orientation, decoration, bedrooms, living_rooms</p>
          </el-alert>
          
          <el-form label-width="100px">
            <el-form-item label="数据来源">
              <el-radio-group v-model="dataSource">
                <el-radio label="government">房管局</el-radio>
                <el-radio label="other">其他</el-radio>
              </el-radio-group>
            </el-form-item>
            
            <el-form-item label="CSV文件">
              <el-upload
                ref="csvUploadRef"
                :auto-upload="false"
                :limit="1"
                accept=".csv"
                :on-change="handleCsvChange"
              >
                <el-button type="primary">选择CSV文件</el-button>
              </el-upload>
            </el-form-item>
            
            <el-form-item>
              <el-button type="success" @click="uploadCsv" :loading="csvUploading">
                导入CSV
              </el-button>
            </el-form-item>
          </el-form>
          
          <el-divider />
          
          <el-form label-width="100px">
            <el-form-item label="Excel文件">
              <el-upload
                ref="excelUploadRef"
                :auto-upload="false"
                :limit="1"
                accept=".xlsx,.xls"
                :on-change="handleExcelChange"
              >
                <el-button type="primary">选择Excel文件</el-button>
              </el-upload>
            </el-form-item>
            
            <el-form-item>
              <el-button type="success" @click="uploadExcel" :loading="excelUploading">
                导入Excel
              </el-button>
            </el-form-item>
          </el-form>
        </el-card>
      </el-col>
      
      <el-col :span="12">
        <el-card>
          <template #header>
            <span>导入模板</span>
          </template>
          
          <el-table :data="templateColumns" border style="width: 100%">
            <el-table-column prop="name" label="字段名" width="150" />
            <el-table-column prop="description" label="说明" />
            <el-table-column prop="example" label="示例" width="150" />
          </el-table>
          
          <div style="margin-top: 20px;">
            <el-button type="primary" @click="downloadTemplate">
              下载CSV模板
            </el-button>
          </div>
        </el-card>
        
        <el-card style="margin-top: 20px;">
          <template #header>
            <span>导入记录</span>
          </template>
          
          <el-timeline>
            <el-timeline-item
              v-for="(record, index) in importRecords"
              :key="index"
              :timestamp="record.time"
              placement="top"
            >
              <el-card>
                <p>文件：{{ record.filename }}</p>
                <p>结果：{{ record.message }}</p>
              </el-card>
            </el-timeline-item>
          </el-timeline>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { dataImportApi } from '../api'

const dataSource = ref('government')
const csvFile = ref(null)
const excelFile = ref(null)
const csvUploading = ref(false)
const excelUploading = ref(false)
const templateColumns = ref([])
const importRecords = ref([])

const handleCsvChange = (file) => {
  csvFile.value = file.raw
}

const handleExcelChange = (file) => {
  excelFile.value = file.raw
}

const uploadCsv = async () => {
  if (!csvFile.value) {
    ElMessage.warning('请先选择CSV文件')
    return
  }
  
  csvUploading.value = true
  try {
    const formData = new FormData()
    formData.append('file', csvFile.value)
    
    const { data } = await dataImportApi.importCsv(formData, dataSource.value)
    ElMessage.success(data.message)
    
    importRecords.value.unshift({
      time: new Date().toLocaleString(),
      filename: csvFile.value.name,
      message: data.message
    })
    
    csvFile.value = null
  } catch (e) {
    ElMessage.error('导入失败：' + (e.response?.data?.detail || e.message))
  } finally {
    csvUploading.value = false
  }
}

const uploadExcel = async () => {
  if (!excelFile.value) {
    ElMessage.warning('请先选择Excel文件')
    return
  }
  
  excelUploading.value = true
  try {
    const formData = new FormData()
    formData.append('file', excelFile.value)
    
    const { data } = await dataImportApi.importExcel(formData, dataSource.value)
    ElMessage.success(data.message)
    
    importRecords.value.unshift({
      time: new Date().toLocaleString(),
      filename: excelFile.value.name,
      message: data.message
    })
    
    excelFile.value = null
  } catch (e) {
    ElMessage.error('导入失败：' + (e.response?.data?.detail || e.message))
  } finally {
    excelUploading.value = false
  }
}

const loadTemplate = async () => {
  try {
    const { data } = await dataImportApi.getTemplate()
    templateColumns.value = data?.columns || []
  } catch (e) {
    console.error('加载模板失败', e)
  }
}

const downloadTemplate = () => {
  const headers = templateColumns.value.map(c => c.name).join(',')
  const examples = templateColumns.value.map(c => c.example || '').join(',')
  const content = headers + '\n' + examples
  
  const blob = new Blob(['\ufeff' + content], { type: 'text/csv;charset=utf-8' })
  const url = window.URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = '房价数据导入模板.csv'
  link.click()
  window.URL.revokeObjectURL(url)
}

onMounted(() => {
  loadTemplate()
})
</script>

<style scoped>
.data-import {
  width: 100%;
}
</style>
