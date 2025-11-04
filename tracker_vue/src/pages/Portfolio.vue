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

      <!-- Portfolio Industry Pie Chart -->
      <div class="industry-pie-chart-section">
        <h2>Portfolio by Industry</h2>
        <div class="charts-section">
          <!-- Value Chart -->
          <div class="chart-subsection">
            <h3>Value by Industry</h3>
            <div v-if="industryChartData.datasets[0].data.length > 0" class="chart-container">
              <Chart type="pie" :data="industryChartData" :options="pieChartOptions" class="small-pie-chart" />
            </div>
            <div v-else-if="!loading" class="empty-chart">
              <p>No industry data available for charting.</p>
            </div>
          </div>

          <!-- Gains Chart -->
          <div class="chart-subsection">
            <h3>{{ getPeriodDisplayName(globalPeriod) }} Gains</h3>
            <div v-if="gainsChartData.datasets[0].data.length > 0" class="chart-container">
              <Chart type="pie" :data="gainsChartData" :options="pieChartOptions" class="small-pie-chart" />
            </div>
            <div v-else-if="!loading" class="empty-chart">
              <p>No gains data for this period.</p>
            </div>
          </div>

          <!-- Losses Chart -->
          <div class="chart-subsection">
            <h3>{{ getPeriodDisplayName(globalPeriod) }} Losses</h3>
            <div v-if="lossesChartData.datasets[0].data.length > 0" class="chart-container">
              <Chart type="pie" :data="lossesChartData" :options="pieChartOptions" class="small-pie-chart" />
            </div>
            <div v-else-if="!loading" class="empty-chart">
              <p>No losses data for this period.</p>
            </div>
          </div>
        </div>
      </div>

      <div class="portfolio-table">
        <div class="table-controls">
          <div class="control-group">
            <div class="global-period-control">
              <label for="global-period-selector">All Holdings Period:</label>
              <select id="global-period-selector" v-model="globalPeriod" @change="updateAllHoldingsPeriod"
                class="global-period-selector">
                <option value="intraday">Intraday</option>
                <option value="1w">1 Week</option>
                <option value="1m">1 Month</option>
                <option value="3m">3 Months</option>
                <option value="6m">6 Months</option>
                <option value="1y">1 Year</option>
                <option value="5y">5 Years</option>
                <option value="all">All Time</option>
              </select>
            </div>
            <div class="hide-unknown-control">
              <label class="checkbox-label">
                <input id="hide-unknown-checkbox" type="checkbox" v-model="hideUnknownHoldings" />
                <span class="checkmark"></span>
                <span>Hide Unknown Holdings</span>
              </label>
            </div>
          </div>
        </div>
        <DataTable v-if="filteredHoldings.length > 0" :value="filteredHoldings" :filters="filters" filterDisplay="row"
          :globalFilterFields="['name', 'symbol', 'isin', 'industry']" :paginator="true" :rows="10"
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

          <Column field="industry" header="Industry" sortable :showFilterMatchModes="false">
            <template #filter="{ filterCallback }">
              <InputText v-model="filters.industry.value" type="text" placeholder="Search by Industry"
                class="p-column-filter" @input="filterCallback()" />
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
                <select :value="slotProps.data.selectedPeriod || globalPeriod"
                  @change="updateHoldingPeriod(slotProps.data, $event.target.value)" class="period-selector">
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
    <Toast />
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
import Toast from 'primevue/toast'
import { useToast } from 'primevue/usetoast'

const toast = useToast()

const periodDefinitions = {
  '1w': 7 * 24 * 60 * 60 * 1000,      // 1 week
  '1m': 30 * 24 * 60 * 60 * 1000,     // 1 month
  '3m': 90 * 24 * 60 * 60 * 1000,     // 3 months
  '6m': 180 * 24 * 60 * 60 * 1000,    // 6 months
  '1y': 365 * 24 * 60 * 60 * 1000,    // 1 year
  '5y': 5 * 365 * 24 * 60 * 60 * 1000 // 5 years
}
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

// Filter transactions by period
const filterTransactionsByPeriod = (transactions, period) => {
  if (!transactions || transactions.length === 0 || period === 'all' || period === 'alltime') {
    return transactions || []
  }

  // Get current timestamp in milliseconds
  const now = Date.now()

  const cutoffTime = now - (periodDefinitions[period] || 0)

  // Transaction timestamps are in milliseconds (Unix timestamp * 1000)
  return transactions.filter(transaction => transaction.timestamp >= cutoffTime)
}

// Process historical data for specific time periods (lazy loading)
const processHistoricalData = (rawHistoryData, requiredPeriods = ['intraday']) => {
  if (!rawHistoryData || rawHistoryData.length === 0) {
    return {}
  }

  // Get current timestamp in seconds (match API format)
  const now = Date.now()


  // Ensure intraday is always included as default
  const periodsToProcess = requiredPeriods.includes('intraday') ?
    requiredPeriods :
    ['intraday', ...requiredPeriods]

  // Filter and format data for each required period
  const filteredData = {}
  periodsToProcess.forEach(key => {
    if (key === 'intraday') {
      // Intraday data is already processed by the API
      return
    }
    if (key === 'all') {
      filteredData['alltime_data'] = [...rawHistoryData]
      return
    }

    if (periodDefinitions[key]) {
      const cutoffTime = now - periodDefinitions[key]
      const startIndex = findFirstIndexGreaterOrEqual(rawHistoryData, cutoffTime)
      const dataKey = getDataKeyForPeriod(key)
      filteredData[dataKey] = rawHistoryData.slice(startIndex)
    }
  })

  return filteredData
}

const chartOptions = ref({
  responsive: true,
  maintainAspectRatio: false,
  plugins: {
    legend: {
      display: false
    },
    tooltip: {
      callbacks: {
        label: function (context) {
          const { quantity, total } = context.raw
          if (context.dataset.label === 'Buy Transactions' || context.dataset.label === 'Sell Transactions') {
            return `Quantity: ${quantity}, Total: €${total}`
          } else {
            return `${context.parsed.y} €`
          }
        },
        title: function (tooltipItems) {
          return `Date: ${tooltipItems[0].label}`
        }
      },
      titleColor: getComputedStyle(document.documentElement).getPropertyValue('--text-color').trim(),
      bodyColor: getComputedStyle(document.documentElement).getPropertyValue('--text-color').trim(),
      backgroundColor: getComputedStyle(document.documentElement).getPropertyValue('--dark-bg').trim()
    }
  },
  scales: {
    x: {
      display: true,
      ticks: {
        color: getComputedStyle(document.documentElement).getPropertyValue('--text-color').trim()
      },
      grid: {
        color: getComputedStyle(document.documentElement).getPropertyValue('--border-light').trim()
      }
    },
    y: {
      display: true,
      ticks: {
        color: getComputedStyle(document.documentElement).getPropertyValue('--text-color').trim(),
        callback: function(value) {
          return '€' + value.toFixed(2);
        }
      },
      grid: {
        color: getComputedStyle(document.documentElement).getPropertyValue('--border-light').trim()
      }
    }
  }
})

const holdings = ref([])
const globalPeriod = ref('intraday')

// Industry pie chart data
const industryChartData = ref({
  labels: [],
  datasets: [{
    data: [],
    backgroundColor: [],
    borderWidth: 1
  }]
})

// Gains and losses chart data
const gainsChartData = ref({
  labels: [],
  datasets: [{
    data: [],
    backgroundColor: [],
    borderWidth: 1
  }]
})

const lossesChartData = ref({
  labels: [],
  datasets: [{
    data: [],
    backgroundColor: [],
    borderWidth: 1
  }]
})

const pieChartOptions = ref({
  responsive: true,
  maintainAspectRatio: false,
  layout: {
  },
  plugins: {
    legend: {
      position: 'bottom',
      labels: {
        // padding: 20,
        usePointStyle: true,
        boxWidth: 12,
        color: getComputedStyle(document.documentElement).getPropertyValue('--text-color').trim(), // Text color for legend labels
        font: {
          size: 12
        }
      },
      maxWidth: undefined, // Allow full width
      maxHeight: undefined // Allow full height
    },
    tooltip: {
      callbacks: {
        label: function (context) {
          const value = context.parsed
          const total = context.dataset.data.reduce((sum, val) => sum + val, 0)
          const percentage = ((value / total) * 100).toFixed(1)
          return `${context.label}: €${value.toFixed(2)} (${percentage}%)`
        }
      },
      titleColor: getComputedStyle(document.documentElement).getPropertyValue('--text-color').trim(), // Text color for tooltip titles
      bodyColor: getComputedStyle(document.documentElement).getPropertyValue('--text-color').trim() // Text color for tooltip body
    }
  }
})

// Update all holdings to use the global period
const updateAllHoldingsPeriod = async () => {
  // Clear individual selections and apply global period
  holdings.value.forEach(holding => {
    // Remove individual period selection to force use of global
    delete holding.selectedPeriod
  })

  // Process historical data for all holdings with the new global period
  if (holdings.value.length > 0) {
    const batchSize = 3
    for (let i = 0; i < holdings.value.length; i += batchSize) {
      const batch = holdings.value.slice(i, i + batchSize)
      const batchPromises = batch.map(async (holding) => {
        if (holding.history && holding.history.length > 0) {
          const dataKey = getDataKeyForPeriod(globalPeriod.value)
          if (!holding[dataKey]) {
            await processHoldingHistoricalData(holding, [globalPeriod.value])
          }
        }
      })
      await Promise.all(batchPromises)
    }
  }

  // Update the gains/losses charts for the new period
  updateGainsLossesCharts()
}

// Update industry pie chart data
const updateIndustryChart = () => {
  const industryMap = new Map()
  const colors = [
    '#FF6384', '#36A2EB', '#FFCE56', '#4BC0C0',
    '#9966FF', '#FF9F40', '#FF6384', '#C9CBCF',
    '#4BC0C0', '#FF6384', '#36A2EB', '#FFCE56'
  ] // Reuse colors if more industries

  // Aggregate holdings by industry
  holdings.value.forEach((holding) => {
    if (holding.industry && holding.industry !== 'Unknown') {
      const industry = holding.industry
      const value = holding.value || 0
      if (!industryMap.has(industry)) {
        industryMap.set(industry, 0)
      }
      industryMap.set(industry, industryMap.get(industry) + value)
    }
  })

  // Convert to chart format
  const labels = []
  const data = []
  const backgroundColors = []

  Array.from(industryMap.entries())
    .sort(([, a], [, b]) => b - a) // Sort by value descending
    .forEach(([industry, value], index) => {
      labels.push(industry)
      data.push(parseFloat(value.toFixed(2)))
      backgroundColors.push(colors[index % colors.length])
    })

  industryChartData.value = {
    labels,
    datasets: [{
      data,
      backgroundColor: backgroundColors,
      borderWidth: 1
    }]
  }
}

// Update gains and losses charts by industry
const updateGainsLossesCharts = () => {
  const gainsMap = new Map()
  const lossesMap = new Map()
  const colors = [
    '#4CAF50', '#8BC34A', '#CDDC39', // Greens for gains
    '#F44336', '#E91E63', '#9C27B0'  // Reds for losses
  ]

  // Calculate gains/losses by industry for the selected period
  holdings.value.forEach((holding) => {
    if (holding.industry && holding.industry !== 'Unknown') {
      const industry = holding.industry
      const changeAmount = periodChangeAmount(holding)
      const holdingValue = holding.value || 0

      // Calculate change as percentage or absolute value based on period
      let changeValue = changeAmount * holdingValue / holding.current_price // Scale change by current value share
      changeValue = parseFloat(changeValue.toFixed(2))

      if (changeValue > 0) {
        // Positive gain
        if (!gainsMap.has(industry)) {
          gainsMap.set(industry, 0)
        }
        gainsMap.set(industry, gainsMap.get(industry) + Math.abs(changeValue))
      } else if (changeValue < 0) {
        // Negative loss (stored as positive for chart)
        if (!lossesMap.has(industry)) {
          lossesMap.set(industry, 0)
        }
        lossesMap.set(industry, lossesMap.get(industry) + Math.abs(changeValue))
      }
    }
  })

  // Update gains chart
  const gainsLabels = []
  const gainsData = []
  const gainsBackgroundColors = []

  Array.from(gainsMap.entries())
    .sort(([, a], [, b]) => b - a)
    .forEach(([industry, gain], index) => {
      gainsLabels.push(industry)
      gainsData.push(parseFloat(gain.toFixed(2)))
      gainsBackgroundColors.push(colors[index % colors.length]) // Use greens
    })

  gainsChartData.value = {
    labels: gainsLabels,
    datasets: [{
      data: gainsData,
      backgroundColor: gainsBackgroundColors,
      borderWidth: 1
    }]
  }

  // Update losses chart
  const lossesLabels = []
  const lossesData = []
  const lossesBackgroundColors = []

  Array.from(lossesMap.entries())
    .sort(([, a], [, b]) => b - a)
    .forEach(([industry, loss], index) => {
      lossesLabels.push(industry)
      lossesData.push(parseFloat(loss.toFixed(2)))
      lossesBackgroundColors.push(colors[3 + (index % 3)]) // Use reds (offset by 3)
    })

  lossesChartData.value = {
    labels: lossesLabels,
    datasets: [{
      data: lossesData,
      backgroundColor: lossesBackgroundColors,
      borderWidth: 1
    }]
  }
}

// New ref for global period change tracking
const hideUnknownHoldings = ref(false)

const filters = reactive({
  global: { value: null, matchMode: FilterMatchMode.CONTAINS },
  name: { value: null, matchMode: FilterMatchMode.CONTAINS },
  isin: { value: null, matchMode: FilterMatchMode.CONTAINS },
  industry: { value: null, matchMode: FilterMatchMode.CONTAINS },
  shares: { value: null, matchMode: FilterMatchMode.BETWEEN },
  avg_price: { value: null, matchMode: FilterMatchMode.BETWEEN },
  current_price: { value: null, matchMode: FilterMatchMode.BETWEEN },
  value: { value: null, matchMode: FilterMatchMode.BETWEEN },
  total_invested: { value: null, matchMode: FilterMatchMode.BETWEEN }
})

// Computed property to filter out unknown holdings
const filteredHoldings = computed(() => {
  if (!hideUnknownHoldings.value) {
    return holdings.value
  }

  return holdings.value.filter(holding => {
    const name = holding.name || ''
    const isNameKnown = name.trim() !== '' &&
      !name.toLowerCase().includes('unknown')

    return isNameKnown
  })
})

// Computed properties for portfolio metrics with memoization (using filtered holdings)
const totalValue = computed(() => filteredHoldings.value.reduce((sum, holding) => sum + holding.value, 0))
const totalGainLoss = computed(() => {
  const totalValueSum = totalValue.value
  const totalInvestedSum = filteredHoldings.value.reduce((sum, holding) => sum + holding.total_invested, 0)
  return totalInvestedSum > 0 ? ((totalValueSum - totalInvestedSum) / totalInvestedSum) * 100 : 0
})
const holdingsCount = computed(() => filteredHoldings.value.length)
const topPerformer = ref('')
const loading = ref(true)
const error = ref('')
const editingIndex = ref(null)
const editingShares = ref(0)
// const isModalOpen = ref(false)
// const selectedHolding = ref({symbol: '', name: '', isin: ''})

const createChartFormat = (rawData, transactionData = [], period = 'intraday') => {
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

  const datasets = [
    {
      label: 'Price',
      data: rawData.map(point => point[1]),
      fill: false,
      borderColor: priceColor,
      pointRadius: 0,
      tension: 0.1
    }
  ]

  // Filter transactions by period
  const periodFilteredTransactions = filterTransactionsByPeriod(transactionData, period)

        // Add transaction dots for Buy transactions (green upward triangle)
        const buyTransactions = periodFilteredTransactions.filter(t => t.sub_type === 'Stock/ETF/Bond Purchase')
  if (buyTransactions.length > 0) {
    const buyPoints = buyTransactions.map(transaction => ({
      x: new Date(transaction.timestamp).toLocaleString([], {
        year: '2-digit', month: '2-digit', day: '2-digit',
      }), // Convert back to seconds for chart
      y: transaction.price,
      quantity: transaction.quantity,
      total: (transaction.quantity * transaction.price + (transaction.fee || 0)).toFixed(2)
    }))

    datasets.push({
      label: 'Buy Transactions',
      data: buyPoints,
      borderColor: '#28a745',
      backgroundColor: '#28a745',
      borderWidth: 1,
      pointStyle: 'triangle',
      pointRadius: 6,
      pointHoverRadius: 8,
      pointRotation: 0, // Triangle pointing up
      showLine: false,
      tension: 0
    })
  }

        // Add transaction dots for Sell transactions (red downward triangle)
        const sellTransactions = periodFilteredTransactions.filter(t => t.type === 'Investment Returns')
        // TODO: Update this to use subtype filtering once subtype is established
  if (sellTransactions.length > 0) {
    const sellPoints = sellTransactions.map(transaction => ({
      x: new Date(transaction.timestamp).toLocaleString([], {
        year: '2-digit', month: '2-digit', day: '2-digit',
      }), // Convert back to seconds for chart
      y: transaction.price,
      quantity: transaction.quantity,
      total: (transaction.quantity * transaction.price + (transaction.fee || 0)).toFixed(2)
    }))
    datasets.push({
      label: 'Sell Transactions',
      data: sellPoints,
      borderColor: '#dc3545',
      backgroundColor: '#dc3545',
      borderWidth: 1,
      pointStyle: 'triangle',
      pointRadius: 6,
      pointHoverRadius: 8,
      pointRotation: 180, // Triangle pointing down
      showLine: false,
      tension: 0
    })
  }
  return {
    labels: rawData.map(point =>
      new Date(point[0]).toLocaleString([], {
        year: '2-digit', month: '2-digit', day: '2-digit',
      })
    ),
    datasets: datasets
  }
}

const setChartData = async () => {
  // Progressive loading: Process holdings in batches for better performance
  const holdingsToProcess = holdings.value
  const batchSize = 3 // Process 3 holdings at a time

  for (let i = 0; i < holdingsToProcess.length; i += batchSize) {
    const batch = holdingsToProcess.slice(i, i + batchSize)

    const batchPromises = batch.map(async (holding) => {
      // Process intraday data first (always needed as default)
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

        const intradayDatasets = [
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

        // Filter transactions by intraday period and add transaction dots for Buy transactions (green upward triangle)
        const periodFilteredBuyTransactions = filterTransactionsByPeriod(holding.transactions || [], 'intraday').filter(t => t.type === 'Buy')
        if (periodFilteredBuyTransactions.length > 0) {
          const buyPoints = periodFilteredBuyTransactions.map(transaction => ({
            x: new Date(transaction.timestamp).toLocaleString([], { hour: '2-digit', minute: '2-digit' }), // Use timestamp directly for chart
            y: transaction.price,
            quantity: transaction.quantity,
            total: (transaction.quantity * transaction.price + (transaction.fee || 0)).toFixed(2)
          }))

          intradayDatasets.push({
            label: 'Buy Transactions',
            data: buyPoints,
            borderColor: '#28a745',
            backgroundColor: '#28a745',
            borderWidth: 1,
            pointStyle: 'triangle',
            pointRadius: 6,
            pointHoverRadius: 8,
            pointRotation: 0, // Triangle pointing up
            showLine: false,
            tension: 0
          })
        }

        // Filter transactions by intraday period and add transaction dots for Sell transactions (red downward triangle)
        const periodFilteredSellTransactions = filterTransactionsByPeriod(holding.transactions || [], 'intraday').filter(t => t.type === 'Sell')
        if (periodFilteredSellTransactions.length > 0) {
          const sellPoints = periodFilteredSellTransactions.map(transaction => ({
            x: new Date(transaction.timestamp).toLocaleString([], { hour: '2-digit', minute: '2-digit' }), // Use timestamp directly for chart
            y: transaction.price,
            quantity: transaction.quantity,
            total: (transaction.quantity * transaction.price + (transaction.fee || 0)).toFixed(2)
          }))

          intradayDatasets.push({
            label: 'Sell Transactions',
            data: sellPoints,
            borderColor: '#dc3545',
            backgroundColor: '#dc3545',
            borderWidth: 1,
            pointStyle: 'triangle',
            pointRadius: 6,
            pointHoverRadius: 8,
            pointRotation: 180, // Triangle pointing down
            showLine: false,
            tension: 0
          })
        }

        holding.intraday_data = {
          labels: holding.intraday_data.map(point =>
            new Date(point[0]).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
          ),
          datasets: intradayDatasets
        }
      }

      // Only process historical data if it exists and has length
      if (holding.history && holding.history.length > 0) {
        // For performance, only compute the default period initially
        await processHoldingHistoricalData(holding, [globalPeriod.value])
      }

      // Yield control to allow UI updates between batches
      if (i < holdingsToProcess.length - batchSize) {
        await new Promise(resolve => setTimeout(resolve, 10))
      }
    })

    // Wait for current batch to complete before moving to next
    await Promise.all(batchPromises)
  }
}

// Process historical data with lazy period computation
const processHoldingHistoricalData = async (holding, requiredPeriods = [globalPeriod.value]) => {
  if (!holding.history || holding.history.length === 0) {
    return
  }

  try {
    const processedData = await processHistoricalDataAsync(holding.history, requiredPeriods)

    // Cache the processed data on the holding object
    Object.keys(processedData).forEach(key => {
      if (processedData[key]) {
        // Extract period from data key
        let periodForKey = 'intraday'
        if (key === 'weekly_data') periodForKey = '1w'
        else if (key === 'monthly_data') periodForKey = '1m'
        else if (key === 'quarterly_data') periodForKey = '3m'
        else if (key === 'semiannual_data') periodForKey = '6m'
        else if (key === 'yearly_data') periodForKey = '1y'
        else if (key === 'fiveyear_data') periodForKey = '5y'
        else if (key === 'alltime_data') periodForKey = 'all'

        holding[key] = createChartFormat(processedData[key], holding.transactions || [], periodForKey)
      }
    })
  } catch (error) {
    console.error(`Error processing historical data for holding ${holding.isin}:`, error)
  }
}

// Async version of processHistoricalData with lazy loading support
const processHistoricalDataAsync = async (rawHistoryData, requiredPeriods = [globalPeriod.value]) => {
  // Use a timeout to yield control for large datasets
  if (rawHistoryData.length > 1000) {
    await new Promise(resolve => setTimeout(resolve, 0))
  }

  return processHistoricalData(rawHistoryData, requiredPeriods)
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

    // Find top performer (stock with highest daily percentage change)
    if (holdings.value.length > 0) {
      const topHolding = holdings.value
        .filter(holding => holding.preday && holding.preday > 0) // Only consider holdings with valid preday
        .reduce((max, holding) => {
          const maxChange = ((max.current_price - max.preday) / max.preday) * 100
          const holdingChange = ((holding.current_price - holding.preday) / holding.preday) * 100
          return holdingChange > maxChange ? holding : max
        }, holdings.value[0])
      topPerformer.value = topHolding ? topHolding.name : ''
    }

    await setChartData()
    updateIndustryChart()
    updateGainsLossesCharts()

  } catch (err) {
    console.error('Error fetching portfolio:', err.response.data.message)
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
      toast.add({ severity: 'warn', summary: 'Invalid Input', detail: 'Please enter a valid number of shares.', life: 5000 });
      return
    }

    if (newShares < 0) {
      toast.add({ severity: 'warn', summary: 'Invalid Input', detail: 'Shares cannot be negative.', life: 5000 });
      return
    }

    loading.value = true
    await adjustHoldingShares(holding.isin, newShares, holding.current_price)
    toast.add({ severity: 'success', summary: 'Success', detail: 'Holding adjusted successfully.', life: 5000 });
    await fetchPortfolio() // Refresh the portfolio data
    editingIndex.value = null // Exit edit mode
    editingShares.value = 0
  } catch (err) {
    console.error('Error adjusting holding:', err)
    toast.add({ severity: 'error', summary: 'Error', detail: 'Failed to adjust holding. Please try again.', life: 5000 });
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

// Old function replaced with debounced version below

// Debounced period update to prevent excessive processing
const updateHoldingPeriod = ((holding, period) => {
  // Debounce periods are cached on holdings to avoid re-processing
  const debounceKey = `debounce_${period}`
  if (holding[debounceKey]) {
    clearTimeout(holding[debounceKey])
  }

  holding[debounceKey] = setTimeout(async () => {
    // If the period matches the global period, clear individual selection
    if (period === globalPeriod.value) {
      delete holding.selectedPeriod
    } else {
      // Override global period with individual selection
      holding.selectedPeriod = period
    }
    delete holding[debounceKey] // Clean up

    // Compute the period data if not already computed
    const dataKey = getDataKeyForPeriod(period)
    if (!holding[dataKey] && holding.history && holding.history.length > 0) {
      await processHoldingHistoricalData(holding, [period])
    }
  }, 200) // 200ms debounce delay
})

const getChartData = (holding) => {
  const period = holding.selectedPeriod || globalPeriod.value
  const dataKey = getDataKeyForPeriod(period)

  // If the period data doesn't exist and we have historical data, compute it
  if (!holding[dataKey] && holding.history && holding.history.length > 0) {
    // Schedule computation for next tick to avoid blocking the render
    setTimeout(() => processHoldingHistoricalData(holding, [period]), 0)
    // Return intraday data as fallback while computing
    return holding.intraday_data
  }

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
  background: #333;
  color: #fff;
  padding: 20px;
  border-radius: 8px;
  text-align: center;
  flex: 1;
  min-width: 200px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.insight-card h3 {
  margin: 0 0 10px 0;
  color: var(--text-color);
  font-size: 14px;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.insight-card p {
  margin: 0;
  font-size: 24px;
  font-weight: bold;
  color: var(--primary-blue);
}



.portfolio-table {
  margin-top: 20px;
}

.table-controls {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  flex-wrap: wrap;
  gap: 15px;
}

.table-controls h2 {
  margin: 0;
  color: var(--text-muted);
  font-size: 1.5rem;
}

.global-period-control {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 12px 16px;
  background: var(--dark-bg);
  border-radius: 8px;
  border: 1px solid var(--border-light);
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.global-period-control label {
  font-weight: 600;
  color: var(--text-muted);
  font-size: 14px;
  margin: 0;
}

.global-period-selector {
  padding: 8px 12px;
  border: 1px solid var(--border-medium);
  border-radius: 4px;
  font-size: 14px;
  font-weight: 500;
  background: var(--white);
  min-width: 120px;
}

.global-period-selector:focus {
  outline: none;
  border-color: var(--primary-blue);
  box-shadow: 0 0 0 2px rgba(0, 123, 255, 0.25);
}

.table-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 10px;
}


.global-filter {
  width: 250px;
  padding: 8px 12px;
  border: 1px solid var(--border-medium);
  border-radius: 4px;
  font-size: 14px;
}

.global-filter:focus {
  outline: none;
  border-color: var(--primary-blue);
  box-shadow: 0 0 0 2px rgba(0, 123, 255, 0.25);
}

.holdings-table {
  border-radius: 8px;
  overflow: hidden;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

:deep(.p-datatable .p-datatable-thead > tr > th) {
  background-color: var(--dark-bg);
  border-bottom: 2px solid var(--border-light);
  font-weight: 600;
  color: var(--text-color) !important;
  padding: 12px 16px;
}

:deep(.p-datatable .p-datatable-tbody > tr > td) {
  padding: 12px 16px;
  border-bottom: 1px solid var(--border-light);
}

:deep(.p-datatable .p-datatable-tbody > tr:hover) {
  background-color: var(--table-hover);
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
  background-color: var(--dark-bg);
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
  color: var(--success-green);
  border-color: var(--success-green);
}

.success-button:hover {
  background-color: var(--success-green);
  border-color: var(--success-green);
}

.secondary-button {
  color: var(--secondary-gray);
  border-color: var(--secondary-gray);
}

.secondary-button:hover {
  background-color: var(--secondary-gray);
  border-color: var(--secondary-gray);
}

.empty-state {
  text-align: center;
  padding: 40px 20px;
  color: var(--secondary-gray);
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
  color: var(--danger-red);
  background-color: var(--error-bg);
  border: 1px solid var(--error-border);
  border-radius: 4px;
}

.symbol-missing {
  display: flex;
  align-items: center;
  gap: 8px;
}

.symbol-missing span {
  color: var(--danger-red);
}

.enter-symbol-button {
  background: none;
  border: none;
  color: var(--primary-blue);
  cursor: pointer;
  font-size: 18px;
  padding: 4px;
  border-radius: 4px;
}

.enter-symbol-button:hover {
  background-color: var(--hover-bg);
}


.p-field {
  margin-bottom: 16px;
}

.p-field label {
  display: block;
  margin-bottom: 4px;
  font-weight: 600;
  color: var(--text-muted);
}

.today-change-card {
  margin-top: 12px;
  padding: 8px 12px;
  background: var(--dark-bg);
  border-radius: 6px;
  border: 1px solid var(--border-light);
  text-align: center;
}

.change-label {
  font-size: 11px;
  color: var(--secondary-gray);
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
  color: var(--success-green);
}

.change-value.negative {
  color: var(--danger-red);
}

.change-value.neutral {
  color: var(--secondary-gray);
}

.change-amount {
  font-size: 12px;
  color: var(--secondary-gray);
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
  border: 1px solid var(--border-medium);
  border-radius: 4px;
  font-size: 14px;
  background: var(--dark-bg);
  color: var(--text-color);
}

.period-selector:focus {
  outline: none;
  border-color: var(--primary-blue);
  box-shadow: 0 0 0 2px rgba(0, 123, 255, 0.25);
}

.performance-chart-wrapper {
  width: 100%;
  height: 140px;
}

.checkbox-label {
  display: flex;
  align-items: center;
  cursor: pointer;
  font-size: 14px;
  color: #495057;
}

.checkbox-label input[type="checkbox"] {
  display: none;
}

.checkbox-label .checkmark {
  width: 18px;
  height: 18px;
  border: 2px solid #007bff;
  border-radius: 3px;
  margin-right: 8px;
  position: relative;
  background: #fff;
  transition: background-color 0.2s ease;
}

.checkbox-label input:checked+.checkmark {
  background: #007bff;
  border-color: #007bff;
}

.checkbox-label input:checked+.checkmark::after {
  content: '';
  position: absolute;
  top: 2px;
  left: 6px;
  width: 4px;
  height: 8px;
  border: solid white;
  border-width: 0 2px 2px 0;
  transform: rotate(45deg);
}

.checkbox-label .checkmark:hover {
  background: rgba(0, 123, 255, 0.1);
}

.checkbox-label input:checked+.checkmark:hover {
  background: #0056b3;
}

.industry-pie-chart-section {
  margin-top: 40px;
  padding: 20px;
  background: var(--dark-bg);
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.industry-pie-chart-section h2 {
  margin: 0 0 20px 0;
  color: var(--text-color);
  font-size: 1.5rem;
  text-align: center;
}

.pie-chart {
  max-width: 800px;
  margin: 0 auto;
  min-height: 600px;
}

.small-pie-chart {
  max-width: 400px;
  margin: 0 auto;
  min-height: 300px;
}

.empty-chart {
  text-align: center;
  padding: 40px 20px;
  color: #6c757d;
  font-style: italic;
}

.empty-chart p {
  margin: 0;
  font-size: 16px;
}

.chart-subsection {
  margin-bottom: 30px;
}

.chart-subsection h3 {
  margin: 0 0 15px 0;
  color: var(--text-color);
  font-size: 1.1rem;
  text-align: center;
}

.gains-losses-section {
  margin-top: 40px;
  display: flex;
  justify-content: center;
  gap: 40px;
  flex-wrap: wrap;
}

.gains-losses-section h3 {
  margin: 0 0 30px 0;
  color: #495057;
  font-size: 1.3rem;
  text-align: center;
}

.charts-section {
  display: flex;
  justify-content: center;
  gap: 40px;
  flex-wrap: wrap;
  align-items: flex-start;
}
</style>
