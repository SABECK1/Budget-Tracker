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
          <!-- <Column field="symbol" header="Symbol" sortable :showFilterMatchModes="false">
            <template #body="slotProps">
              <div v-if="slotProps.data.symbol !== 'Not found'" class="symbol-display">
                {{ slotProps.data.symbol }}
              </div>
              <div v-else class="symbol-missing">
                <span>{{ slotProps.data.symbol }}</span>
                <button @click="openModal(slotProps.data)" class="enter-symbol-button" title="Enter symbol manually">
                  <i class="pi pi-plus"></i>
                </button>
              </div>
            </template>
            <template #filter="{ filterCallback }">
              <InputText
                v-model="filters.symbol.value"
                type="text"
                placeholder="Search by Symbol"
                class="p-column-filter"
                @input="filterCallback()"
              />
            </template>
          </Column> -->

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
import { ref, onMounted, reactive } from 'vue'
import AppNavigation from '../components/navigation.vue'
import axios from 'axios'
import Cookies from 'js-cookie'
import DataTable from 'primevue/datatable'
import Column from 'primevue/column'
import InputText from 'primevue/inputtext'
import InputNumber from 'primevue/inputnumber'
import Button from 'primevue/button'
import { FilterMatchMode } from '@primevue/core/api'

const holdings = ref([])
const totalValue = ref(0)
const totalGainLoss = ref(0)
const holdingsCount = ref(0)
const topPerformer = ref('')
const loading = ref(true)
const error = ref('')
const editingIndex = ref(null)
const editingShares = ref(0)
// const isModalOpen = ref(false)
// const selectedHolding = ref({symbol: '', name: '', isin: ''})

// Filters for DataTable
const filters = reactive({
  global: { value: null, matchMode: FilterMatchMode.CONTAINS },
  name: { value: null, matchMode: FilterMatchMode.CONTAINS },
  // symbol: { value: null, matchMode: FilterMatchMode.CONTAINS },
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

// const openModal = (holding) => {
//   selectedHolding.value = { ...holding }
//   isModalOpen.value = true
// }

// const saveSymbol = async () => {
//   if (!selectedHolding.value.name.trim()) {
//     alert("Name is required")
//     return
//   }

//   try {
//     const response = await axios.post(`${process.env.VUE_APP_API_BASE_URL}/save-symbol/`, {
//       isin: selectedHolding.value.isin,
//       // symbol: selectedHolding.value.symbol.trim(),
//       name: selectedHolding.value.name.trim() || ""
//     }, {
//       headers: {
//         'Content-Type': 'application/json',
//         "X-CSRFToken": Cookies.get('csrftoken'),
//       },
//       withCredentials: true,
//     })

//     if (response.status === 200) {
//       isModalOpen.value = false
//       fetchPortfolio() // refresh the portfolio to show the new symbol
//     }
//   } catch (err) {
//     console.error('Error saving symbol:', err)
//     alert("Failed to save symbol. Please try again.")
//   }
// }

// // DataTable handles filtering internally with the filters reactive object

const startEdit = (data, index) => {
  editingIndex.value = index
  editingShares.value = data.shares
  console.log('Editing shares for', data.isin, 'to', editingShares.value, "at index", index)
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
</style>
