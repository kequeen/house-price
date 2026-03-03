import axios from 'axios'

const api = axios.create({
  baseURL: '/api',
  timeout: 30000
})

export const transactionApi = {
  getList(params) {
    return api.get('/transactions', { params })
  },
  
  getMonthlyStats(params) {
    return api.get('/transactions/stats/monthly', { params })
  },
  
  getRegionStats(params) {
    return api.get('/transactions/stats/regions', { params })
  },
  
  getPriceTrend(params) {
    return api.get('/transactions/trends/price', { params })
  },
  
  getVolumeTrend(params) {
    return api.get('/transactions/trends/volume', { params })
  },
  
  getRegions() {
    return api.get('/transactions/regions/list')
  },
  
  getDistricts(region) {
    return api.get(`/transactions/districts/${region}`)
  },
  
  getYears() {
    return api.get('/transactions/years')
  }
}

export const dataImportApi = {
  importCsv(formData, dataSource = 'government') {
    return api.post(`/data/import/csv?data_source=${dataSource}`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    })
  },
  
  importExcel(formData, dataSource = 'government') {
    return api.post(`/data/import/excel?data_source=${dataSource}`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    })
  },
  
  getTemplate() {
    return api.get('/data/template')
  }
}

export const crawlerApi = {
  start(city, regions, pages) {
    const params = new URLSearchParams({ city, pages })
    if (regions) params.append('regions', regions)
    return api.post(`/crawler/start?${params}`)
  },
  
  getStatus() {
    return api.get('/crawler/status')
  },
  
  getCities() {
    return api.get('/crawler/cities')
  }
}

export default api
