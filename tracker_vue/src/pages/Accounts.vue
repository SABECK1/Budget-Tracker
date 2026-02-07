<template>
  <AppNavigation />
  <ProtectedLayout>
  <div class="accounts-page">
    <h1>Bank Accounts</h1>
    <div v-if="loading" class="loading">Loading accounts...</div>
    <div v-else>
      <div class="accounts-widget">
        <div class="widget-header">
          <h2>Your Bank Accounts</h2>
          <Button label="Add Account" icon="pi pi-plus" @click="showAddDialog = true" class="p-button-success p-button-small" />
        </div>
        <DataTable v-if="accounts.length > 0" :value="accounts" :paginator="true" :rows="10"
                   :rowsPerPageOptions="[5, 10, 25, 50]" paginatorTemplate="RowsPerPageDropdown FirstPageLink PrevPageLink CurrentPageReport NextPageLink LastPageLink"
                   currentPageReportTemplate="Showing {first} to {last} of {totalRecords} accounts" class="accounts-table">
          <Column field="name" header="Account Name" sortable>
            <template #body="slotProps">
              {{ slotProps.data.name }}
            </template>
          </Column>
          <Column field="iban" header="IBAN" sortable>
            <template #body="slotProps">
              {{ slotProps.data.iban }}
            </template>
          </Column>
          <Column field="account_type_display" header="Account Type" sortable>
            <template #body="slotProps">
              {{ slotProps.data.account_type_display || 'Not specified' }}
            </template>
          </Column>
          <Column field="bic" header="BIC" sortable>
            <template #body="slotProps">
              {{ slotProps.data.bic }}
            </template>
          </Column>
          <Column header="Actions">
            <template #body="slotProps">
              <Button icon="pi pi-pencil" class="p-button-rounded p-button-text p-button-info p-button-sm" @click="editAccount(slotProps.data)" title="Edit" />
              <Button icon="pi pi-trash" class="p-button-rounded p-button-text p-button-danger p-button-sm" @click="confirmDelete(slotProps.data)" title="Delete" />
            </template>
          </Column>
          <template #empty>
            <div class="empty-state">
              <p>No accounts found. Add your first bank account.</p>
            </div>
          </template>
        </DataTable>
        <div v-else class="empty-state">
          <p>No accounts found. Add your first bank account.</p>
        </div>
      </div>
    </div>

    <!-- Add/Edit Account Dialog -->
    <Dialog v-model:visible="showAddDialog" :header="editingAccount ? 'Edit Account' : 'Add New Account'" modal style="width: 450px">
      <form @submit.prevent="saveAccount">
        <div class="p-field">
          <label for="name">Account Name</label>
          <InputText id="name" v-model="accountForm.name" required :class="{ 'p-invalid': formErrors.name }" />
          <small v-if="formErrors.name" class="p-error">{{ formErrors.name }}</small>
        </div>
        <div class="p-field">
          <label for="iban">IBAN</label>
          <InputText id="iban" v-model="accountForm.iban" :class="{ 'p-invalid': formErrors.iban }" />
          <small v-if="formErrors.iban" class="p-error">{{ formErrors.iban }}</small>
        </div>
        <div class="p-field">
          <label for="bic">BIC</label>
          <InputText id="bic" v-model="accountForm.bic" :class="{ 'p-invalid': formErrors.bic }" />
          <small v-if="formErrors.bic" class="p-error">{{ formErrors.bic }}</small>
        </div>
        <div class="p-field">
          <label for="account_type">Account Type (only necessary for CSV-Upload)</label>
          <Dropdown id="account_type" v-model="accountForm.account_type" :options="accountTypeOptions" optionLabel="label" optionValue="value" placeholder="Select account type" :class="{ 'p-invalid': formErrors.account_type }" />
          <small v-if="formErrors.account_type" class="p-error">{{ formErrors.account_type }}</small>
        </div>
        <div class="p-field">
          <label for="bank_name">Bank Name</label>
          <InputText id="bank_name" v-model="accountForm.bank_name" :class="{ 'p-invalid': formErrors.bank_name }" />
          <small v-if="formErrors.bank_name" class="p-error">{{ formErrors.bank_name }}</small>
        </div>
      </form>
      <template #footer>
        <Button label="Cancel" icon="pi pi-times" class="p-button-text" @click="closeDialog" />
        <Button label="Save" icon="pi pi-check" class="p-button-primary" @click="saveAccount" />
      </template>
    </Dialog>

    <!-- Delete Confirmation Dialog -->
    <Dialog v-model:visible="showDeleteDialog" header="Confirm Delete" modal>
      <p>Are you sure you want to delete the account "{{ accountToDelete?.name }}"?</p>
      <p class="p-mt-2"><strong>This action cannot be undone.</strong></p>
      <template #footer>
        <Button label="Cancel" icon="pi pi-times" class="p-button-text" @click="showDeleteDialog = false" />
        <Button label="Delete" icon="pi pi-check" class="p-button-danger" @click="deleteAccount" />
      </template>
    </Dialog>
  </div>
  </ProtectedLayout>
</template>

<script setup>
import { ref, onMounted, reactive } from 'vue'
import AppNavigation from '../components/navigation.vue'
import axios from 'axios'
import Cookies from 'js-cookie'
import DataTable from 'primevue/datatable'
import Column from 'primevue/column'
import Button from 'primevue/button'
import InputText from 'primevue/inputtext'
import Dropdown from 'primevue/dropdown'
import Dialog from 'primevue/dialog'
import { useToast } from 'primevue/usetoast'
import ProtectedLayout from '@/components/ProtectedLayout.vue'
import { useAuthStore } from '@/store/auth'
import '../assets/css/main.css'

const toast = useToast()

const accounts = ref([])
const loading = ref(true)
const error = ref('')
const showAddDialog = ref(false)
const showDeleteDialog = ref(false)
const editingAccount = ref(null)
const accountToDelete = ref(null)

const accountForm = reactive({
  name: '',
  iban: '',
  bic: '',
  bank_name: '',
  account_type: ''
})

const formErrors = reactive({
  name: '',
  iban: '',
  bic: '',
  bank_name: '',
  account_type: ''
})

const accountTypeOptions = [
  { label: 'Trade Republic', value: 'trade_republic' },
  { label: 'Volksbank', value: 'volksbank' }
]

// Fetch accounts from API
const fetchAccounts = async () => {
  try {
    loading.value = true
    error.value = ''

    const response = await axios.get(`${process.env.VUE_APP_API_BASE_URL}/bankaccounts/`, {
      headers: {
        'Content-Type': 'application/json',
        "X-CSRFToken": Cookies.get('csrftoken'),
      },
      withCredentials: true,
    })
    accounts.value = response.data || []
  } catch (err) {
    console.error('Error fetching accounts:', err)
    error.value = 'Failed to load bank accounts. Please try again.'
    toast.add({ severity: 'error', summary: 'Error', detail: 'Failed to load bank accounts.', life: 5000 })
  } finally {
    loading.value = false
  }
}

// Save account (create or update)
const saveAccount = async () => {
  try {
    // Clear errors
    Object.keys(formErrors).forEach(key => {
      formErrors[key] = ''
    })

    // Validate form
    if (!accountForm.name.trim()) {
      formErrors.name = 'Account name is required'
      return
    }

    const url = editingAccount.value?.url || `${process.env.VUE_APP_API_BASE_URL}/bankaccounts/`
    const method = editingAccount.value ? 'put' : 'post'

    console.log('Saving account:', { url, method, data: accountForm, csrf: Cookies.get('csrftoken') })

    const response = await axios[method](url, accountForm, {
      headers: {
        'Content-Type': 'application/json',
        "X-CSRFToken": Cookies.get('csrftoken'),
      },
      withCredentials: true,
    })

    console.log('Response:', response)

    if (response.status === 200 || response.status === 201) {
      toast.add({
        severity: 'success',
        summary: 'Success',
        detail: editingAccount.value ? 'Account updated successfully.' : 'Account created successfully.',
        life: 5000
      })
      closeDialog()
      fetchAccounts()
    }
  } catch (err) {
    console.error('Error saving account:', err)
    console.error('Response status:', err.response?.status)
    console.error('Response data:', err.response?.data)

    const errors = err.response?.data || {}

    // Check for specific error scenarios
    if (err.response?.status === 400) {
      console.log('Bad request error - likely validation issues')
    } else if (err.response?.status === 401 || err.response?.status === 403) {
      toast.add({ severity: 'error', summary: 'Authentication Error', detail: 'Please log in again.', life: 5000 })
      return
    } else if (err.response?.status === 500) {
      toast.add({ severity: 'error', summary: 'Server Error', detail: 'Try again later or contact support.', life: 5000 })
      return
    }

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
        detail: `Failed to ${editingAccount.value ? 'update' : 'create'} account. Please try again.`,
        life: 5000
      })
    }
  }
}

// Edit account
const editAccount = (account) => {
  editingAccount.value = account
  accountForm.name = account.name
  accountForm.iban = account.iban || ''
  accountForm.bic = account.bic || ''
  accountForm.bank_name = account.bank_name || ''
  accountForm.account_type = account.account_type || ''
  showAddDialog.value = true
}

// Confirm delete
const confirmDelete = (account) => {
  accountToDelete.value = account
  showDeleteDialog.value = true
}

// Delete account
const deleteAccount = async () => {
  try {
    await axios.delete(accountToDelete.value.url, {
      headers: {
        "X-CSRFToken": Cookies.get('csrftoken'),
      },
      withCredentials: true,
    })
    toast.add({ severity: 'success', summary: 'Success', detail: 'Account deleted successfully.', life: 5000 })
    fetchAccounts()
    showDeleteDialog.value = false
    accountToDelete.value = null
  } catch (err) {
    console.error('Error deleting account:', err)
    toast.add({ severity: 'error', summary: 'Error', detail: 'Failed to delete account.', life: 5000 })
  }
}

// Close dialog and reset form
const closeDialog = () => {
  showAddDialog.value = false
  editingAccount.value = null
  accountForm.name = ''
  accountForm.iban = ''
  accountForm.bic = ''
  accountForm.bank_name = ''
  accountForm.account_type = ''
  Object.keys(formErrors).forEach(key => {
    formErrors[key] = ''
  })
}

onMounted(() => {
  const authStore = useAuthStore();
  
  // Only fetch if the store says we are actually logged in
  if (authStore.isAuthenticated) {
    fetchAccounts();
  }
})
</script>

<style scoped>
.accounts-page {
  padding: 20px;
}

.accounts-widget {
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

.accounts-table {
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
</style>
