<template>
  <AppNavigation />
  <ProtectedLayout>
  <div class="budgets-page">
    <h1>Budgets</h1>
    <div v-if="loading" class="loading">Loading budgets...</div>
    <div v-else>
      <div class="budgets-widget">
        <div class="widget-header">
          <h2>Your Budgets</h2>
          <Button label="Add Budget" icon="pi pi-plus" @click="showAddDialog = true" class="p-button-success p-button-small" />
        </div>
        <DataTable v-if="budgets.length > 0" :value="budgets" :paginator="true" :rows="10"
                   :rowsPerPageOptions="[5, 10, 25, 50]" paginatorTemplate="RowsPerPageDropdown FirstPageLink PrevPageLink CurrentPageReport NextPageLink LastPageLink"
                   currentPageReportTemplate="Showing {first} to {last} of {totalRecords} budgets" class="budgets-table">
          <Column field="name" header="Budget Name" sortable>
            <template #body="slotProps">
              {{ slotProps.data.name }}
            </template>
          </Column>
          <Column field="period" header="Period" sortable>
            <template #body="slotProps">
              {{ formatPeriod(slotProps.data.period) }}
            </template>
          </Column>
          <Column field="limit_amount" header="Limit Amount" sortable>
            <template #body="slotProps">
              {{ formatCurrency(slotProps.data.limit_amount) }}
            </template>
          </Column>
          <Column field="spent_amount" header="Spent Amount" sortable>
            <template #body="slotProps">
              {{ formatCurrency(slotProps.data.spent_amount) }}
            </template>
          </Column>
          <Column field="remaining_amount" header="Remaining Amount" sortable>
            <template #body="slotProps">
              {{ formatCurrency(slotProps.data.remaining_amount) }}
            </template>
          </Column>
          <Column field="spent_percentage" header="Usage" sortable>
            <template #body="slotProps">
              {{ Math.round(slotProps.data.spent_percentage) }}%
            </template>
          </Column>
          <Column header="Transaction Types">
            <template #body="slotProps">
              <div class="type-subtype-container">
                <div v-if="slotProps.data.transaction_types && slotProps.data.transaction_types.length > 0" class="types-list">
                  <span v-for="type in getTransactionTypesForBudget(slotProps.data)" :key="type.id" class="type-badge">
                    {{ type.name }}
                  </span>
                </div>
                <div v-else class="no-data-text">No types assigned</div>
              </div>
            </template>
          </Column>
          <Column header="Transaction Subtypes">
            <template #body="slotProps">
              <div class="type-subtype-container">
                <div v-if="slotProps.data.transaction_subtypes && slotProps.data.transaction_subtypes.length > 0" class="subtypes-list">
                  <span v-for="subtype in getTransactionSubtypesForBudget(slotProps.data)" :key="subtype.id" class="subtype-badge">
                    {{ subtype.name }}
                  </span>
                </div>
                <div v-else class="no-data-text">No subtypes assigned</div>
              </div>
            </template>
          </Column>
          <Column header="Actions">
            <template #body="slotProps">
              <Button icon="pi pi-pencil" class="p-button-rounded p-button-text p-button-info p-button-sm" @click="editBudget(slotProps.data)" title="Edit" />
              <Button icon="pi pi-trash" class="p-button-rounded p-button-text p-button-danger p-button-sm" @click="confirmDelete(slotProps.data)" title="Delete" />
            </template>
          </Column>
          <template #empty>
            <div class="empty-state">
              <p>No budgets found. Create your first budget to start tracking your spending.</p>
            </div>
          </template>
        </DataTable>
        <div v-else class="empty-state">
          <p>No budgets found. Create your first budget to start tracking your spending.</p>
        </div>
      </div>
    </div>

    <!-- Add/Edit Budget Dialog -->
    <Dialog v-model:visible="showAddDialog" :header="editingBudget ? 'Edit Budget' : 'Add New Budget'" modal style="width: 500px">
      <form @submit.prevent="saveBudget">
        <div class="p-field">
          <label for="name">Budget Name</label>
          <InputText id="name" v-model="budgetForm.name" required :class="{ 'p-invalid': formErrors.name }" />
          <small v-if="formErrors.name" class="p-error">{{ formErrors.name }}</small>
        </div>
        <div class="p-field">
          <label for="limit_amount">Limit Amount</label>
          <InputNumber id="limit_amount" v-model="budgetForm.limit_amount" mode="currency" currency="EUR" locale="de-DE" :class="{ 'p-invalid': formErrors.limit_amount }" />
          <small v-if="formErrors.limit_amount" class="p-error">{{ formErrors.limit_amount }}</small>
        </div>
        <div class="p-field">
          <label for="period">Period</label>
          <Dropdown id="period" v-model="budgetForm.period" :options="periodOptions" optionLabel="label" optionValue="value" placeholder="Select period" @change="handlePeriodChange" :class="{ 'p-invalid': formErrors.period }" />
          <small v-if="formErrors.period" class="p-error">{{ formErrors.period }}</small>
        </div>
        <div v-if="budgetForm.period === 'custom'" class="p-field">
          <label for="custom_period_days">Custom Period (days)</label>
          <InputNumber id="custom_period_days" v-model="budgetForm.custom_period_days" :min="1" :class="{ 'p-invalid': formErrors.custom_period_days }" />
          <small v-if="formErrors.custom_period_days" class="p-error">{{ formErrors.custom_period_days }}</small>
        </div>
        <div class="p-field">
          <label for="transaction_types">Transaction Types</label>
          <MultiSelect id="transaction_types" v-model="budgetForm.transaction_types" :options="transactionTypes" optionLabel="name" optionValue="id" placeholder="Select transaction types" @change="filterSubtypes" :class="{ 'p-invalid': formErrors.transaction_types }" />
          <small v-if="formErrors.transaction_types" class="p-error">{{ formErrors.transaction_types }}</small>
        </div>
        <div class="p-field">
          <label for="transaction_subtypes">Transaction Subtypes</label>
          <MultiSelect id="transaction_subtypes" v-model="budgetForm.transaction_subtypes" :options="availableSubtypes" optionLabel="name" optionValue="id" placeholder="Select transaction subtypes" :class="{ 'p-invalid': formErrors.transaction_subtypes }" />
          <small v-if="formErrors.transaction_subtypes" class="p-error">{{ formErrors.transaction_subtypes }}</small>
        </div>
      </form>
      <template #footer>
        <Button label="Cancel" icon="pi pi-times" class="p-button-text" @click="closeDialog" />
        <Button label="Save" icon="pi pi-check" class="p-button-primary" @click="saveBudget" />
      </template>
    </Dialog>

    <!-- Delete Confirmation Dialog -->
    <Dialog v-model:visible="showDeleteDialog" header="Confirm Delete" modal>
      <p>Are you sure you want to delete the budget "{{ budgetToDelete?.name }}"?</p>
      <p class="p-mt-2"><strong>This action cannot be undone.</strong></p>
      <template #footer>
        <Button label="Cancel" icon="pi pi-times" class="p-button-text" @click="showDeleteDialog = false" />
        <Button label="Delete" icon="pi pi-check" class="p-button-danger" @click="deleteBudget" />
      </template>
    </Dialog>
  </div>
  </ProtectedLayout>
</template>

<script setup>
import { ref, onMounted, reactive, computed } from 'vue'
import AppNavigation from '../components/navigation.vue'
import axios from 'axios'
import Cookies from 'js-cookie'
import DataTable from 'primevue/datatable'
import Column from 'primevue/column'
import Button from 'primevue/button'
import InputText from 'primevue/inputtext'
import InputNumber from 'primevue/inputnumber'
import Dropdown from 'primevue/dropdown'
import MultiSelect from 'primevue/multiselect'
import Dialog from 'primevue/dialog'
import { useToast } from 'primevue/usetoast'
import ProtectedLayout from '@/components/ProtectedLayout.vue'
import { useAuthStore } from '@/store/auth'
import '../assets/css/main.css'

const toast = useToast()

const budgets = ref([])
const transactionTypes = ref([])
const transactionSubtypes = ref([])
const loading = ref(true)
const error = ref('')
const showAddDialog = ref(false)
const showDeleteDialog = ref(false)
const editingBudget = ref(null)
const budgetToDelete = ref(null)

const budgetForm = reactive({
  name: '',
  limit_amount: 0,
  period: 'monthly',
  custom_period_days: null,
  transaction_types: [],
  transaction_subtypes: []
})

const formErrors = reactive({
  name: '',
  limit_amount: '',
  period: '',
  custom_period_days: '',
  transaction_types: '',
  transaction_subtypes: ''
})

const periodOptions = [
  { label: 'Daily', value: 'daily' },
  { label: 'Weekly', value: 'weekly' },
  { label: 'Monthly', value: 'monthly' },
  { label: 'Yearly', value: 'yearly' },
  { label: 'Custom', value: 'custom' }
]

// Computed property to filter subtypes based on selected transaction types
const availableSubtypes = computed(() => {
  if (!budgetForm.transaction_types) {
    return transactionSubtypes.value
  }
  
  return transactionSubtypes.value.filter(subtype => 
    budgetForm.transaction_types.includes(subtype.transaction_type)
  )
})


// Filter subtypes when transaction types change
const filterSubtypes = () => {
  // Remove any selected subtypes that are no longer available
  if (budgetForm.transaction_subtypes && budgetForm.transaction_subtypes.length > 0) {
    const filteredSubtypes = availableSubtypes.value.map(s => s.id)
    
    budgetForm.transaction_subtypes = budgetForm.transaction_subtypes.filter(id => 
      filteredSubtypes.includes(id)
    )
  }
}

// Fetch budgets from API
const fetchBudgets = async () => {
  try {
    loading.value = true
    error.value = ''

    const response = await axios.get(`${process.env.VUE_APP_API_BASE_URL}/budgets/`, {
      headers: {
        'Content-Type': 'application/json',
        "X-CSRFToken": Cookies.get('csrftoken'),
      },
      withCredentials: true,
    })
    
    budgets.value = response.data || []
    
  } catch (err) {
    console.error('Error fetching budgets:', err)
    console.error('Error response:', err.response)
    console.error('Error status:', err.response?.status)
    console.error('Error data:', err.response?.data)
    
    if (err.response?.status === 401 || err.response?.status === 403) {
      console.error('Authentication error - user may not be logged in or session expired')
      error.value = 'Authentication failed. Please log in again.'
      toast.add({ severity: 'error', summary: 'Authentication Error', detail: 'Please log in again.', life: 5000 })
    } else {
      error.value = 'Failed to load budgets. Please try again.'
      toast.add({ severity: 'error', summary: 'Error', detail: 'Failed to load budgets.', life: 5000 })
    }
  } finally {
    loading.value = false
  }
}

// Fetch transaction types
const fetchTransactionTypes = async () => {
  try {
    const response = await axios.get(`${process.env.VUE_APP_API_BASE_URL}/transactiontypes/`, {
      headers: {
        'Content-Type': 'application/json',
        "X-CSRFToken": Cookies.get('csrftoken'),
      },
      withCredentials: true,
    })
    transactionTypes.value = response.data || []
  } catch (err) {
    console.error('Error fetching transaction types:', err)
    toast.add({ severity: 'error', summary: 'Error', detail: 'Failed to load transaction types.', life: 5000 })
  }
}

// Fetch transaction subtypes
const fetchTransactionSubtypes = async () => {
  try {
    const response = await axios.get(`${process.env.VUE_APP_API_BASE_URL}/transactionsubtypes/`, {
      headers: {
        'Content-Type': 'application/json',
        "X-CSRFToken": Cookies.get('csrftoken'),
      },
      withCredentials: true,
    })
    transactionSubtypes.value = response.data || []
  } catch (err) {
    console.error('Error fetching transaction subtypes:', err)
    toast.add({ severity: 'error', summary: 'Error', detail: 'Failed to load transaction subtypes.', life: 5000 })
  }
}

// Save budget (create or update)
const saveBudget = async () => {
  try {
    // Clear errors
    Object.keys(formErrors).forEach(key => {
      formErrors[key] = ''
    })

    // Validate form
    if (!budgetForm.name.trim()) {
      formErrors.name = 'Budget name is required'
      return
    }

    if (!budgetForm.limit_amount || budgetForm.limit_amount <= 0) {
      formErrors.limit_amount = 'Limit amount must be greater than 0'
      return
    }

    if (budgetForm.period === 'custom' && (!budgetForm.custom_period_days || budgetForm.custom_period_days <= 0)) {
      formErrors.custom_period_days = 'Custom period days must be greater than 0'
      return
    }

    const url = editingBudget.value?.url || `${process.env.VUE_APP_API_BASE_URL}/budgets/`
    const method = editingBudget.value ? 'put' : 'post'

    const response = await axios[method](url, budgetForm, {
      headers: {
        'Content-Type': 'application/json',
        "X-CSRFToken": Cookies.get('csrftoken'),
      },
      withCredentials: true,
    })

    if (response.status === 200 || response.status === 201) {
      toast.add({
        severity: 'success',
        summary: 'Success',
        detail: editingBudget.value ? 'Budget updated successfully.' : 'Budget created successfully.',
        life: 5000
      })
      closeDialog()
      fetchBudgets()
    }
  } catch (err) {
    console.error('Error saving budget:', err)
    console.error('Response status:', err.response?.status)
    console.error('Response data:', err.response?.data)

    const errors = err.response?.data || {}

    if (errors.non_field_errors) {
      toast.add({ severity: 'error', summary: 'Validation Error', detail: errors.non_field_errors.join(', '), life: 5000 })
    } else if (Object.keys(errors).length > 0) {
      // Show field-specific errors
      let errorMessage = 'Please fix the errors:'
      Object.keys(errors).forEach(key => {
        if (Object.prototype.hasOwnProperty.call(formErrors, key)) {
          formErrors[key] = errors[key].join(', ')
          errorMessage += ` ${key}: ${errors[key].join(', ')}`
        }
      })
      toast.add({ severity: 'error', summary: 'Validation Error', detail: errorMessage, life: 5000 })
    } else {
      // Generic error
      toast.add({
        severity: 'error',
        summary: 'Error',
        detail: `Failed to ${editingBudget.value ? 'update' : 'create'} budget. Please try again.`,
        life: 5000
      })
    }
  }
}

// Edit budget
const editBudget = (budget) => {
  editingBudget.value = budget
  budgetForm.name = budget.name
  budgetForm.limit_amount = budget.limit_amount
  budgetForm.period = budget.period
  budgetForm.custom_period_days = budget.custom_period_days
  budgetForm.transaction_types = budget.transaction_types.map(t => t.id)
  budgetForm.transaction_subtypes = budget.transaction_subtypes.map(s => s.id)
  showAddDialog.value = true
}

// Confirm delete
const confirmDelete = (budget) => {
  budgetToDelete.value = budget
  showDeleteDialog.value = true
}

// Delete budget
const deleteBudget = async () => {
  try {
    await axios.delete(budgetToDelete.value.url, {
      headers: {
        "X-CSRFToken": Cookies.get('csrftoken'),
      },
      withCredentials: true,
    })
    toast.add({ severity: 'success', summary: 'Success', detail: 'Budget deleted successfully.', life: 5000 })
    fetchBudgets()
    showDeleteDialog.value = false
    budgetToDelete.value = null
  } catch (err) {
    console.error('Error deleting budget:', err)
    toast.add({ severity: 'error', summary: 'Error', detail: 'Failed to delete budget.', life: 5000 })
  }
}

// Close dialog and reset form
const closeDialog = () => {
  showAddDialog.value = false
  editingBudget.value = null
  budgetForm.name = ''
  budgetForm.limit_amount = 0
  budgetForm.period = 'monthly'
  budgetForm.custom_period_days = null
  budgetForm.transaction_types = []
  budgetForm.transaction_subtypes = []
  Object.keys(formErrors).forEach(key => {
    formErrors[key] = ''
  })
}

// Handle period change
const handlePeriodChange = () => {
  if (budgetForm.period !== 'custom') {
    budgetForm.custom_period_days = null
  }
}

// Currency formatting function
const formatCurrency = (amount) => {
  if (amount === null || amount === undefined) {
    return '€0.00';
  }
  return new Intl.NumberFormat('de-DE', {
    style: 'currency',
    currency: 'EUR',
    minimumFractionDigits: 2,
    maximumFractionDigits: 2
  }).format(amount);
}

const formatPeriod = (period) => {
  const periodMap = {
    'daily': 'Daily',
    'weekly': 'Weekly',
    'monthly': 'Monthly',
    'yearly': 'Yearly',
    'custom': 'Custom'
  }
  return periodMap[period] || period
}

// Helper methods to get transaction types and subtypes for a budget
const getTransactionTypesForBudget = (budget) => {
  if (!budget.transaction_types || budget.transaction_types.length === 0) {
    return []
  }

      return budget.transaction_types.map(id => {
        const found = transactionTypes.value.find(type => type.id === id)
        return found || { id: id, name: `Unknown Type (${id})` }
      })
}

const getTransactionSubtypesForBudget = (budget) => {
  if (!budget.transaction_subtypes || budget.transaction_subtypes.length === 0) {
    return []
  }

  return budget.transaction_subtypes.map(id => {
        const found = transactionSubtypes.value.find(subtype => subtype.id === id)
        return found || { id: id, name: `Unknown Subtype (${id})` }
      })

}

onMounted(() => {
  const authStore = useAuthStore();
  
  // Only fetch if the store says we are actually logged in
  if (authStore.isAuthenticated) {
    fetchBudgets();
    fetchTransactionTypes();
    fetchTransactionSubtypes();
  }
})
</script>

<style scoped>
.budgets-page {
  padding: 20px;
}

.budgets-widget {
  background: var(--dark-bg);
  color: var(--text-color);
  border-radius: 8px;
  padding: 20px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.widget-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.widget-header h2 {
  margin: 0;
}

.budgets-table {
  border-radius: 8px;
  overflow: hidden;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

:deep(.p-datatable .p-datatable-thead > tr > th) {
  /* background-color: var(--true-black); */
  /* border-bottom: 2px solid #dee2e6; */
  font-weight: 600;
  color: (--text-color);
  padding: 12px 16px;
}

:deep(.p-datatable .p-datatable-tbody > tr > td) {
  padding: 12px 16px;
  /* border-bottom: 1px solid #dee2e6; */
}

:deep(.p-datatable .p-datatable-tbody > tr:hover) {
  background-color: var(--body-bg);
}

:deep(.p-paginator) {
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

.p-field {
  margin-bottom: 16px;
}

.p-field label {
  display: block;
  margin-bottom: 4px;
  font-weight: 600;
  color: var(--text-color)
}

/* Type and Subtype Display Styles */
.type-subtype-container {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.types-list,
.subtypes-list {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.type-badge,
.subtype-badge {
  display: inline-block;
  padding: 4px 8px;
  border-radius: 12px;
  font-size: 12px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  border: 1px solid var(--border-medium);
  background-color: var(--body-bg);
  color: var(--text-color);
  transition: all 0.2s ease;
}

.type-badge:hover,
.subtype-badge:hover {
  background-color: var(--primary-blue);
  color: white;
  border-color: var(--primary-blue);
  transform: translateY(-1px);
}

.no-data-text {
  font-size: 12px;
  color: var(--secondary-gray);
  font-style: italic;
  padding: 4px 8px;
  background-color: var(--body-bg);
  border-radius: 4px;
  border: 1px solid var(--border-medium);
}
</style>