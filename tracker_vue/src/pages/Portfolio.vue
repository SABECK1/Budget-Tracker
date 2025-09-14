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
        <DataTable
          v-if="holdings.length > 0"
          :value="holdings"
          :filters="filters"
          filterDisplay="menu"
          :globalFilterFields="['symbol', 'isin']"
          :paginator="true"
          :rows="10"
          :rowsPerPageOptions="[5, 10, 25, 50]"
          paginatorTemplate="RowsPerPageDropdown FirstPageLink PrevPageLink CurrentPageReport NextPageLink LastPageLink"
          currentPageReportTemplate="Showing {first} to {last} of {totalRecords} holdings"
          responsiveLayout="scroll"
          class="holdings-table"
          sortMode="multiple"
        >
          <template #header>
            <div class="table-header">
              <h3>Portfolio Holdings</h3>
            </div>
          </template>

          <Column field="symbol" header="Symbol" sortable :showFilterMatchModes="false">
            <template #filter="{ filterModel }">
              <InputText
                v-model="filterModel.value"
                type="text"
                placeholder="Search by Symbol"
                class="p-column-filter"
              />
            </template>
          </Column>

          <Column field="isin" header="ISIN" sortable :showFilterMatchModes="false">
            <template #filter="{ filterModel }">
              <InputText
                v-model="filterModel.value"
                type="text"
                placeholder="Search by ISIN"
                class="p-column-filter"
              />
            </template>
          </Column>

          <Column field="shares" header="Shares" sortable dataType="numeric">
            <template #body="slotProps">
              {{ slotProps.data.shares.toFixed(2) }}
            </template>
          </Column>

          <Column field="avg_price" header="Avg Price" sortable dataType="numeric">
            <template #body="slotProps">
              ${{ slotProps.data.avg_price.toFixed(2) }}
            </template>
          </Column>

          <Column field="current_price" header="Current Price" sortable dataType="numeric">
            <template #body="slotProps">
              ${{ slotProps.data.current_price.toFixed(2) }}
            </template>
          </Column>

          <Column field="value" header="Value" sortable dataType="numeric">
            <template #body="slotProps">
              ${{ slotProps.data.value.toFixed(2) }}
            </template>
          </Column>

          <Column field="total_invested" header="Total Invested" sortable dataType="numeric">
            <template #body="slotProps">
              ${{ slotProps.data.total_invested.toFixed(2) }}
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
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, reactive } from 'vue'
import AppNavigation from '../components/navigation.vue'
import axios from 'axios'
import Cookies from 'js-cookie'
import DataTable from 'primevue/datatable'
import Column from 'primevue/column'
import InputText from 'primevue/inputtext'
import { FilterMatchMode } from '@primevue/core/api'

const holdings = ref([])
const totalValue = ref(0)
const totalGainLoss = ref(0)
const holdingsCount = ref(0)
const topPerformer = ref('')
const loading = ref(true)
const error = ref('')

// Filters for DataTable
const filters = reactive({
  symbol: { value: null, matchMode: FilterMatchMode.CONTAINS },
  isin: { value: null, matchMode: FilterMatchMode.CONTAINS },
  shares: { value: null, matchMode: FilterMatchMode.BETWEEN },
  avg_price: { value: null, matchMode: FilterMatchMode.BETWEEN },
  current_price: { value: null, matchMode: FilterMatchMode.BETWEEN },
  value: { value: null, matchMode: FilterMatchMode.BETWEEN },
  total_invested: { value: null, matchMode: FilterMatchMode.BETWEEN }
})

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

// DataTable handles filtering internally with the filters reactive object

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
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
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

.holdings-table {
  border-radius: 8px;
  overflow: hidden;
  box-shadow: 0 2px 8px rgba(0,0,0,0.1);
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

:deep(.p-paginator) {
  background-color: #f8f9fa;
  border-top: 1px solid #dee2e6;
  padding: 12px 16px;
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

.loading, .error {
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
</style>
