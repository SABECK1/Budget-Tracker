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
        <table v-if="holdings.length > 0">
          <thead>
            <tr>
              <th>ISIN</th>
              <th>Shares</th>
              <th>Avg Price</th>
              <th>Current Price</th>
              <th>Value</th>
              <th>Total Invested</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="holding in holdings" :key="holding.isin">
              <td>{{ holding.isin }}</td>
              <td>{{ holding.shares.toFixed(2) }}</td>
              <td>${{ holding.avg_price.toFixed(2) }}</td>
              <td>${{ holding.current_price.toFixed(2) }}</td>
              <td>${{ holding.value.toFixed(2) }}</td>
              <td>${{ holding.total_invested.toFixed(2) }}</td>
            </tr>
          </tbody>
        </table>
        <p v-else>No holdings found. Import some stock transactions to see your portfolio.</p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import AppNavigation from '../components/navigation.vue'
import axios from 'axios'
import Cookies from 'js-cookie'

const holdings = ref([])
const totalValue = ref(0)
const totalGainLoss = ref(0)
const holdingsCount = ref(0)
const topPerformer = ref('')
const loading = ref(true)
const error = ref('')

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

  } catch (err) {
    console.error('Error fetching portfolio:', err)
    error.value = 'Failed to load portfolio data. Please try again.'
  } finally {
    loading.value = false
  }
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
}

.insight-card {
  background: #f0f0f0;
  padding: 20px;
  border-radius: 8px;
  text-align: center;
  flex: 1;
}

.portfolio-table table {
  width: 100%;
  border-collapse: collapse;
}

.portfolio-table th, .portfolio-table td {
  border: 1px solid #ddd;
  padding: 8px;
  text-align: left;
}

.portfolio-table th {
  background-color: #f2f2f2;
}
</style>
