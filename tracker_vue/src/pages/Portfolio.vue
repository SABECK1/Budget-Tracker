<template>
  <AppNavigation />
  <div class="portfolio-page">
    <h1>Stock Portfolio</h1>
    <div v-if="loading" class="loading">Loading portfolio...</div>
    <div v-else-if="error" class="error">{{ error }}</div>
    <div v-else>
      <div class="portfolio-insights">
        <div class="insight-card">
          <h3>Total Value</h3>
          <p>${{ totalValue.toFixed(2) }}</p>
        </div>
        <div class="insight-card">
          <h3>Total Gain/Loss</h3>
          <p>{{ totalGainLoss.toFixed(2) }}%</p>
        </div>
        <div class="insight-card">
          <h3>Holdings Count</h3>
          <p>{{ holdingsCount }}</p>
        </div>
        <div class="insight-card">
          <h3>Top Performer</h3>
          <p>{{ topPerformer || 'N/A' }}</p>
        </div>
      </div>



      <div class="portfolio-table">
        <h2>Your Holdings</h2>
        <DataTable v-if="holdings.length > 0" :value="holdings" :filters="filters" filterDisplay="row"
          :globalFilterFields="['name', 'symbol', 'isin']" :paginator="true" :rows="10"
          :rowsPerPageOptions="[5, 10, 25, 50]"
          paginatorTemplate="RowsPerPageDropdown FirstPageLink PrevPageLink CurrentPageReport NextPageLink LastPageLink"
          currentPageReportTemplate="Showing {first} to {last} of {totalRecords} holdings" responsiveLayout="scroll"
          class="holdings-table" sortMode="multiple">
          <template #header>
            <div class="table-header">
              <h3>Portfolio Holdings</h3>
              <InputText v-model="filters['global'].value" placeholder="Global Search" class="global-filter" />
            </div>
          </template>

          <Column field="name" header="Name" sortable :showFilterMatchModes="false">
            <template #filter="{ filterCallback }">
              <InputText v-model="filters.name.value" type="text" placeholder="Search by name" class="p-column-filter"
                @input="filterCallback()" />
            </template>
          </Column>

          <Column field="isin" header="ISIN" sortable :showFilterMatchModes="false">
            <template #filter="{ filterCallback }">
              <InputText v-model="filters.isin.value" type="text" placeholder="Search by ISIN" class="p-column-filter"
                @input="filterCallback()" />
            </template>
          </Column>

          <Column field="shares" header="Shares" sortable dataType="numeric">
            <template #body="slotProps">
              <div class="shares-display" v-if="editingIndex !== slotProps.index">
                <span>{{ slotProps.data.shares.toFixed(2) }}</span>
                <Button icon="pi pi-pencil" @click="startEdit(slotProps.data, slotProps.index)"
                  class="p-button-rounded p-button-text p-button-sm edit-button" title="Edit shares" />
              </div>
              <div v-else class="shares-editor">
                <InputNumber v-model="editingShares" mode="decimal" :min="0" :maxFractionDigits="2"
                  class="inline-editor" />
                <Button icon="pi pi-check" @click="saveEdit(slotProps.data)"
                  class="p-button-rounded p-button-text p-button-sm success-button" title="Save" />
                <Button icon="pi pi-times" @click="cancelEdit"
                  class="p-button-rounded p-button-text p-button-sm secondary-button" title="Cancel" />
              </div>
            </template>
          </Column>

          <Column field="avg_price" header="Avg Price" sortable dataType="numeric">
            <template #body="slotProps">
              {{ slotProps.data.avg_price.toFixed(2) }}€
            </template>
          </Column>

          <Column field="current_price" header="Current Price" sortable dataType="numeric">
            <template #body="slotProps">
              {{ slotProps.data.current_price.toFixed(2) }}€
            </template>
          </Column>

          <Column field="performance" header="Performance" style="min-width: 220px;">
            <template #body="slotProps">
              <div class="chart-container">
                <select :value="slotProps.data.selectedPeriod || globalPeriod" @change="updateHoldingPeriod(slotProps.data, $event.target.value)" class="period-selector">
                  <option value="intraday">Intraday</option>
                  <option value="1w">1 Week</option>
                  <option value="1m">1 Month</option>
                  <option value="3m">3 Months</option>
                  <option value="6m">6 Months</option>
                  <option value="1y">1 Year</option>
                  <option value="5y">5 Years</option>
                  <option value="all">All Time</option>
                </select>
                <div class="performance-chart-wrapper">
                  <Chart type="line" :data="getChartData(slotProps.data)" :options="chartOptions" />
                </div>
                <div class="today-change-card" v-if="hasPeriodData(slotProps.data)">
                  <div class="change-label">
                    {{ getPeriodDisplayName(slotProps.data.selectedPeriod || globalPeriod) }} Change
                  </div>
                  <div class="change-value" :class="periodChangeClass(slotProps.data)">
                    {{ periodChangePercentage(slotProps.data).toFixed(2) }}%
                  </div>
                  <div class="change-amount">
                    {{ periodChangeAmount(slotProps.data).toFixed(2) }}€
                  </div>
                </div>
              </div>
            </template>
          </Column>

          <Column field="value" header="Value" sortable dataType="numeric">
            <template #body="slotProps">
              {{ slotProps.data.value.toFixed(2) }}€
            </template>
          </Column>

          <Column field="total_invested" header="Total Invested" sortable dataType="numeric">
            <template #body="slotProps">
              {{ slotProps.data.total_invested.toFixed(2) }}€
            </template>
          </Column>

          <template #empty>
            <div class="empty-state">
              <p>No holdings found. Import some stock transactions to see your portfolio.</p>
            </div>
          </template>
        </DataTable>
        <div v-else class="empty-state">
          <p>No holdings found. Import some stock transactions to see your portfolio.</p>
        </div>
      </div>

      <!-- <Dialog v-model:visible="isModalOpen" header="Enter Symbol Manually" modal>
        <div class="p-field">
          <label for="symbol-input">Symbol:</label>
          <InputText id="symbol-input" v-model="selectedHolding.symbol" />
        </div>
        <div class="p-field">
          <label for="name-input">Name:</label>
          <InputText id="name-input" v-model="selectedHolding.name" />
        </div>
        <template #footer>
          <Button label="Cancel" icon="pi pi-times" class="p-button-text" @click="isModalOpen = false"></Button>
          <Button label="Save" icon="pi pi-check" class="p-button-primary" @click="saveSymbol"></Button>
        </template>
      </Dialog> -->
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, reactive } from 'vue'
import AppNavigation from '../components/navigation.vue'
import axios from 'axios'
import Cookies from 'js-cookie'
import DataTable from 'primevue/datatable'
import Column from 'primevue/column'
import InputText from 'primevue/inputtext'
import InputNumber from 'primevue/inputnumber'
import Button from 'primevue/button'
import { FilterMatchMode } from '@primevue/core/api'
import Chart from 'primevue/chart'
// import { set } from 'core-js/core/dict'

// Binary search helper function to find first index where point[0] >= cutoffTime
const findFirstIndexGreaterOrEqual = (data, cutoffTime) => {
  let left = 0
  let right = data.length

  while (left < right) {
    const mid = Math.floor((left + right) / 2)
    if (data[mid][0] < cutoffTime) {
      left = mid + 1
    } else {
      right = mid
    }
  }

  return left
}

// Process historical data for different time periods
const processHistoricalData = (rawHistoryData) => {
  if (!rawHistoryData || rawHistoryData.length === 0) {
    return {
      weekly_data: [],
      monthly_data: [],
      quarterly_data: [],
      semiannual_data: [],
      yearly_data: [],
      fiveyear_data: [],
      alltime_data: []
    }
  }

  // Optimized with binary search for finding cutoff indices

  // Get current timestamp in seconds (match API format)
  const now = Date.now()

  // Time periods in milliseconds
  const periods = {
    '1w': 7 * 24 * 60 * 60 * 1000,      // 1 week
    '1m': 30 * 24 * 60 * 60 * 1000,     // 1 month
    '3m': 90 * 24 * 60 * 60 * 1000,     // 3 months
    '6m': 180 * 24 * 60 * 60 * 1000,    // 6 months
    '1y': 365 * 24 * 60 * 60 * 1000,    // 1 year
    '5y': 5 * 365 * 24 * 60 * 60 * 1000 // 5 years
  }

  // Filter and format data for each period
  const filteredData = {}
  // Filter data points that are within each time period (rawHistoryData is [timestamp, price] pairs)
  // Since data is sorted from oldest to newest, use binary search to find the start index for each cutoff and slice
  Object.keys(periods).forEach(key => {
    const cutoffTime = now - periods[key]
    // Find the first index where point[0] (timestamp) >= cutoffTime using binary search
    const startIndex = findFirstIndexGreaterOrEqual(rawHistoryData, cutoffTime)
    filteredData[key] = rawHistoryData.slice(startIndex)
  })

  // All time data is the full history
  filteredData['alltime'] = [...rawHistoryData]
  return {
    weekly_data: filteredData['1w'],
    monthly_data: filteredData['1m'],
    quarterly_data: filteredData['3m'],
    semiannual_data: filteredData['6m'],
    yearly_data: filteredData['1y'],
    fiveyear_data: filteredData['5y'],
    alltime_data: filteredData['alltime']
  }
}

const chartOptions = ref({
  responsive: true,
  maintainAspectRatio: false,
  plugins: {
    legend: {
      display: false
    }
  },
  scales: {
    x: {
      display: true
    },
    y: {
      display: true
    }
  }
})

const holdings = ref([])
const globalPeriod = ref('intraday')

// Filters for DataTable
const filters = reactive({
  global: { value: null, matchMode: FilterMatchMode.CONTAINS },
  name: { value: null, matchMode: FilterMatchMode.CONTAINS },
  isin: { value: null, matchMode: FilterMatchMode.CONTAINS },
  shares: { value: null, matchMode: FilterMatchMode.BETWEEN },
  avg_price: { value: null, matchMode: FilterMatchMode.BETWEEN },
  current_price: { value: null, matchMode: FilterMatchMode.BETWEEN },
  value: { value: null, matchMode: FilterMatchMode.BETWEEN },
  total_invested: { value: null, matchMode: FilterMatchMode.BETWEEN }
})

// Computed properties for portfolio metrics with memoization
const totalValue = computed(() => holdings.value.reduce((sum, holding) => sum + holding.value, 0))
const totalGainLoss = computed(() => {
  const totalValueSum = totalValue.value
  const totalInvestedSum = holdings.value.reduce((sum, holding) => sum + holding.total_invested, 0)
  return totalInvestedSum > 0 ? ((totalValueSum - totalInvestedSum) / totalInvestedSum) * 100 : 0
})
const holdingsCount = computed(() => holdings.value.length)
const topPerformer = computed(() =>
  holdings.value.length > 0 ? holdings.value.reduce((max, holding) => holding.value > max.value ? holding : max).isin : ''
)
const loading = ref(true)
const error = ref('')
const editingIndex = ref(null)
const editingShares = ref(0)
// const isModalOpen = ref(false)
// const selectedHolding = ref({symbol: '', name: '', isin: ''})

const createChartFormat = (rawData) => {
  if (!rawData || rawData.length === 0) {
    return {
      labels: [],
      datasets: [{
        label: 'Price',
        data: [],
        borderColor: '#6c757d',
        fill: false,
        pointRadius: 0,
        tension: 0.1
      }]
    }
  }

  // Determine color based on trend
  let priceColor = '#6c757d'
  if (rawData[rawData.length - 1][1] - rawData[0][1] > 0) {
    priceColor = '#28a745' // green
  } else {
    priceColor = '#dc3545' // red
  }

  return {
    labels: rawData.map(point =>
      new Date(point[0]).toLocaleString([], {
        year: '2-digit', month: '2-digit', day: '2-digit',
      })
    ),
    datasets: [
      {
        label: 'Price',
        data: rawData.map(point => point[1]),
        fill: false,
        borderColor: priceColor,
        pointRadius: 0,
        tension: 0.1
      }
    ]
  }
}

const setChartData = async () => {
  // Process all holdings asynchronously in parallel for better performance
  const processingPromises = holdings.value.map(async (holding) => {
    // Process historical data into different time periods
    if (holding.history && holding.history.length > 0) {
      const processedData = await processHistoricalDataAsync(holding.history)
      Object.keys(processedData).forEach(key => {
        holding[key] = createChartFormat(processedData[key], holding)
      })
    }

    // Process intraday data
    if (holding.intraday_data && holding.intraday_data.length > 0) {
      // Determine color based on trend
      const lastPrice = holding.intraday_data[holding.intraday_data.length - 1][1]
      let priceColor = '#6c757d'
      if (holding.preday) {
        if (lastPrice > holding.preday) {
          priceColor = '#28a745' // green
        } else if (lastPrice < holding.preday) {
          priceColor = '#dc3545' // red
        }
      }

      holding.intraday_data = {
        labels: holding.intraday_data.map(point =>
          new Date(point[0] * 1000).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
        ),
        datasets: [
          {
            label: 'Price',
            data: holding.intraday_data.map(point => point[1]),
            fill: false,
            borderColor: priceColor,
            pointRadius: 0,
            tension: 0.1
          },
          {
            label: 'Pre-market',
            data: holding.intraday_data.map(() => holding.preday),
            fill: false,
            borderColor: '#FFA726',
            pointRadius: 0,
            borderDash: [5, 5],
            tension: 0.1,
          }
        ]
      }
    }
  })

  // Wait for all holdings to be processed in parallel
  await Promise.all(processingPromises)
}

// Async version of processHistoricalData to support parallel processing
const processHistoricalDataAsync = async (rawHistoryData) => {
  // Use a timeout to yield control and allow other processing
  if (rawHistoryData.length > 1000) {
    await new Promise(resolve => setTimeout(resolve, 0))
  }

  return processHistoricalData(rawHistoryData)
}

const fetchPortfolio = async () => {
  try {
    loading.value = true
    error.value = ''

    const response = await axios.get(`${process.env.VUE_APP_API_BASE_URL}/portfolio/`, {
      headers: {
        'Content-Type': 'application/json',
        "X-CSRFToken": Cookies.get('csrftoken'),
      },
      withCredentials: true,
    })
    const data = response.data

    holdings.value = data.holdings || []
    totalValue.value = data.total_value || 0
    totalGainLoss.value = data.total_gain_loss || 0
    holdingsCount.value = data.holdings_count || 0

    // Find top performer (stock with highest value)
    if (holdings.value.length > 0) {
      const topHolding = holdings.value.reduce((max, holding) =>
        holding.value > max.value ? holding : max
      )
      topPerformer.value = topHolding.isin
    }

    await setChartData()

  } catch (err) {
    console.error('Error fetching portfolio:', err)
    error.value = 'Failed to load portfolio data. Please try again.'
  } finally {
    loading.value = false
  }
}

// // DataTable handles filtering internally with the filters reactive object

const startEdit = (data, index) => {
  editingIndex.value = index
  editingShares.value = data.shares
}

const saveEdit = async (holding) => {
  try {
    const newShares = parseFloat(editingShares.value)

    if (isNaN(newShares)) {
      alert('Please enter a valid number of shares')
      return
    }

    if (newShares < 0) {
      alert('Shares cannot be negative')
      return
    }

    loading.value = true
    await adjustHoldingShares(holding.isin, newShares, holding.current_price)
    await fetchPortfolio() // Refresh the portfolio data
    editingIndex.value = null // Exit edit mode
    editingShares.value = 0
  } catch (err) {
    console.error('Error adjusting holding:', err)
    alert('Failed to adjust holding. Please try again.')
    fetchPortfolio() // Revert changes by refreshing
  } finally {
    loading.value = false
  }
}

const cancelEdit = () => {
  editingIndex.value = null
  editingShares.value = 0
}

const adjustHoldingShares = async (isin, newShares, currentPrice) => {
  const response = await axios.post(`${process.env.VUE_APP_API_BASE_URL}/adjust-holding/`, {
    isin: isin,
    new_shares: newShares,
    current_price: currentPrice,
    note: 'Adjusted holding manually'
  }, {
    headers: {
      'Content-Type': 'application/json',
      "X-CSRFToken": Cookies.get('csrftoken'),
    },
    withCredentials: true,
  })

  if (response.status !== 200) {
    throw new Error('Failed to adjust holding')
  }
}

// Calculate change for selected period
const periodChangeAmount = (holding) => {
  const period = holding.selectedPeriod || globalPeriod.value
  const dataKey = getDataKeyForPeriod(period)
  const periodData = holding[dataKey]

  if (!periodData || !periodData.datasets || periodData.datasets.length === 0) {
    return 0
  }

  const prices = periodData.datasets[0].data
  if (prices.length < 2) return 0 // Need at least 2 data points

  const previousPrice = prices[0]
  return holding.current_price - previousPrice
}

const periodChangePercentage = (holding) => {
  const period = holding.selectedPeriod || globalPeriod.value
  const dataKey = getDataKeyForPeriod(period)
  const periodData = holding[dataKey]

  if (!periodData || !periodData.datasets || periodData.datasets.length === 0) {
    return 0
  }

  const prices = periodData.datasets[0].data
  if (prices.length < 2) return 0 // Need at least 2 data points

  const previousPrice = prices[0]
  if (previousPrice === 0) return 0 // Avoid division by zero

  const change = periodChangeAmount(holding)
  return (change / previousPrice) * 100
}

// Class for period-specific change
const periodChangeClass = (holding) => {
  const change = periodChangeAmount(holding)
  if (change > 0) return 'positive'
  if (change < 0) return 'negative'
  return 'neutral'
}

// Get readable period name for display
const getPeriodDisplayName = (period) => {
  const displayNames = {
    intraday: 'Intraday',
    '1w': 'This Week',
    '1m': 'This Month',
    '3m': 'This Quarter',
    '6m': 'This 6 Months',
    '1y': 'This Year',
    '5y': 'This 5 Years',
    'all': 'All Time'
  }
  return displayNames[period] || 'Period'
}

// Check if holding has data for the current period
const hasPeriodData = (holding) => {
  const period = holding.selectedPeriod || globalPeriod.value
  const dataKey = getDataKeyForPeriod(period)
  const periodData = holding[dataKey]

  if (!periodData || !periodData.datasets || periodData.datasets.length === 0) {
    return false
  }

  const prices = periodData.datasets[0].data
  return prices && prices.length >= 2 // Need at least 2 data points for comparison
}

const updateHoldingPeriod = (holding, period) => {
  holding.selectedPeriod = period
  // Don't need to re-render, Vue will handle it with reactivity
}

const getChartData = (holding) => {
  const period = holding.selectedPeriod || globalPeriod.value
  const dataKey = getDataKeyForPeriod(period)
  return holding[dataKey] || holding.intraday_data
}

const getDataKeyForPeriod = (period) => {
  const mapping = {
    intraday: 'intraday_data',
    '1w': 'weekly_data',
    '1m': 'monthly_data',
    '3m': 'quarterly_data',
    '6m': 'semiannual_data',
    '1y': 'yearly_data',
    '5y': 'fiveyear_data',
    'all': 'alltime_data'
  }
  return mapping[period] || 'intraday_data'
}

onMounted(() => {
  fetchPortfolio()
})
</script>

<style scoped>
.portfolio-page {
  padding: 20px;
}

.portfolio-insights {
  display: flex;
  gap: 20px;
  margin-bottom: 30px;
  flex-wrap: wrap;
}

.insight-card {
  background: #f8f9fa;
  padding: 20px;
  border-radius: 8px;
  text-align: center;
  flex: 1;
  min-width: 200px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.insight-card h3 {
  margin: 0 0 10px 0;
  color: #495057;
  font-size: 14px;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.insight-card p {
  margin: 0;
  font-size: 24px;
  font-weight: bold;
  color: #007bff;
}



.portfolio-table {
  margin-top: 20px;
}

.table-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 10px;
}

.table-header h3 {
  margin: 0;
  color: #495057;
}

.global-filter {
  width: 250px;
  padding: 8px 12px;
  border: 1px solid #ced4da;
  border-radius: 4px;
  font-size: 14px;
}

.global-filter:focus {
  outline: none;
  border-color: #007bff;
  box-shadow: 0 0 0 2px rgba(0, 123, 255, 0.25);
}

.holdings-table {
  border-radius: 8px;
  overflow: hidden;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

:deep(.p-datatable .p-datatable-thead > tr > th) {
  background-color: #f8f9fa;
  border-bottom: 2px solid #dee2e6;
  font-weight: 600;
  color: #495057;
  padding: 12px 16px;
}

:deep(.p-datatable .p-datatable-tbody > tr > td) {
  padding: 12px 16px;
  border-bottom: 1px solid #dee2e6;
}

:deep(.p-datatable .p-datatable-tbody > tr:hover) {
  background-color: #f8f9fa;
}

:deep(.p-datatable .p-datatable-tbody > tr > td.p-cell-editing) {
  background-color: rgba(123, 255, 184, 0.1);
  padding: 0;
}

:deep(.p-datatable .p-datatable-tbody > tr > td.p-cell-editing .p-inputnumber-input) {
  border: none;
  border-radius: 0;
  background-color: transparent;
  padding: 12px 16px;
  font-size: inherit;
  font-family: inherit;
}

:deep(.p-paginator) {
  background-color: #f8f9fa;
  border-top: 1px solid #dee2e6;
  padding: 12px 16px;
}

.shares-display {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.edit-button {
  margin-left: auto;
  opacity: 0.7;
}

.edit-button:hover {
  opacity: 1;
}

.shares-editor {
  display: flex;
  align-items: center;
  gap: 8px;
}

.inline-editor {
  width: 120px !important;
}

.success-button {
  color: #28a745;
  border-color: #28a745;
}

.success-button:hover {
  background-color: #28a745;
  border-color: #28a745;
}

.secondary-button {
  color: #6c757d;
  border-color: #6c757d;
}

.secondary-button:hover {
  background-color: #6c757d;
  border-color: #6c757d;
}

.empty-state {
  text-align: center;
  padding: 40px 20px;
  color: #6c757d;
  font-style: italic;
}

.empty-state p {
  margin: 0;
  font-size: 16px;
}

.loading,
.error {
  text-align: center;
  padding: 40px 20px;
  font-size: 16px;
}

.error {
  color: #dc3545;
  background-color: #f8d7da;
  border: 1px solid #f5c6cb;
  border-radius: 4px;
}

.symbol-missing {
  display: flex;
  align-items: center;
  gap: 8px;
}

.symbol-missing span {
  color: #dc3545;
}

.enter-symbol-button {
  background: none;
  border: none;
  color: #007bff;
  cursor: pointer;
  font-size: 18px;
  padding: 4px;
  border-radius: 4px;
}

.enter-symbol-button:hover {
  background-color: #e9ecef;
}


.p-field {
  margin-bottom: 16px;
}

.p-field label {
  display: block;
  margin-bottom: 4px;
  font-weight: 600;
  color: #495057;
}

.today-change-card {
  margin-top: 12px;
  padding: 8px 12px;
  background: #f8f9fa;
  border-radius: 6px;
  border: 1px solid #dee2e6;
  text-align: center;
}

.change-label {
  font-size: 11px;
  color: #6c757d;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  font-weight: 600;
  margin-bottom: 4px;
  margin-top: 2px;
}

.change-value {
  font-weight: bold;
  font-size: 13px;
  margin-bottom: 2px;
}

.change-value.positive {
  color: #28a745;
}

.change-value.negative {
  color: #dc3545;
}

.change-value.neutral {
  color: #6c757d;
}

.change-amount {
  font-size: 12px;
  color: #6c757d;
  margin-top: 2px;
}

.chart-container {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.period-selector {
  width: 100%;
  padding: 8px 12px;
  border: 1px solid #ced4da;
  border-radius: 4px;
  font-size: 14px;
  background: #fff;
}

.period-selector:focus {
  outline: none;
  border-color: #007bff;
  box-shadow: 0 0 0 2px rgba(0, 123, 255, 0.25);
}

.performance-chart-wrapper {
  width: 100%;
  height: 140px;
}
</style>
