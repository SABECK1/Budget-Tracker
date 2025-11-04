<script setup>
import { ref, onMounted, computed, defineEmits } from "vue";
import FileUpload from 'primevue/fileupload';
import ProgressSpinner from 'primevue/progressspinner';
import Dropdown from 'primevue/dropdown';
import { useToast } from 'primevue/usetoast';
import axios from "axios";
import Cookies from 'js-cookie';

// Define emits
const emit = defineEmits(['upload-success']);

axios.defaults.xsrfCookieName = "csrftoken";
axios.defaults.xsrfHeaderName = "X-CSRFToken";
axios.defaults.withCredentials = true;

const toast = useToast();
const loading = ref(false);
const bankAccounts = ref([]);
const selectedBankAccount = ref(null);
const showValidation = ref(false);

const uploadUrl = computed(() => {
    return selectedBankAccount.value ? `${process.env.VUE_APP_API_BASE_URL}/upload-csv/` : '';
});

// Fetch bank accounts on component mount
const fetchBankAccounts = async () => {
    try {
        const response = await axios.get(`${process.env.VUE_APP_API_BASE_URL}/bankaccounts/`, {
            headers: {
                'Content-Type': 'application/json',
                "X-CSRFToken": Cookies.get('csrftoken'),
            },
            withCredentials: true,
        });
        bankAccounts.value = response.data || [];
    } catch (error) {
        console.error('Error fetching bank accounts:', error);
    }
};

const onUpload = async (event) => {
    const file = event.files[0];
    if (!file) return;

    if (!selectedBankAccount.value) {
        showValidation.value = true;
        return;
    }

    loading.value = true;
    showValidation.value = false;

    const formData = new FormData();
    formData.append("file", file);
    formData.append("bank_account", selectedBankAccount.value);

    try {
        const response = await axios.post(`${process.env.VUE_APP_API_BASE_URL}/upload-csv/`, formData, {
            headers: {
                "Content-Type": "multipart/form-data",
                'X-CSRFToken': Cookies.get('csrftoken'),
            },
            credentials: 'include',
        });

        toast.add({
            severity: 'success',
            summary: 'Success',
            detail: response.data.status || 'CSV uploaded successfully',
            life: 5000
        });

        // Emit event to refresh data in parent component
        emit('upload-success');
    } catch (error) {
        toast.add({
            severity: 'error',
            summary: 'Error',
            detail: error.message,
            life: 5000
        });
    } finally {
        loading.value = false;
    }
};

onMounted(() => {
    fetchBankAccounts();
});
</script>
<template>
    <div class="csv-upload-section">
        <div class="filter-item">
            <label for="bankAccount" class="filter-label">Select Bank Account</label>
            <Dropdown
                id="bankAccount"
                v-model="selectedBankAccount"
                :options="bankAccounts"
                optionLabel="name"
                optionValue="id"
                placeholder="Choose a bank account"
                class="filter-dropdown"
                :class="{ 'p-invalid': !selectedBankAccount && showValidation }"
            />
            <small v-if="!selectedBankAccount && showValidation" class="p-error">Bank account is required</small>
        </div>

        <div class="upload-area">
            <FileUpload
                name="file"
                :url="uploadUrl"
                accept=".csv"
                :withCredentials="true"
                :customUpload="true"
                @uploader="onUpload"
                :disabled="loading || !selectedBankAccount"
            >
                <template #empty>
                    <div class="upload-placeholder">
                        <i class="pi pi-upload text-4xl text-primary mb-3"></i>
                        <p class="text-lg">{{ selectedBankAccount ? 'Drag and drop a CSV file here' : 'Please select a bank account first' }}</p>
                        <p class="text-sm text-gray-600" v-if="selectedBankAccount">Or click to browse and select a file</p>
                    </div>
                </template>
            </FileUpload>
        </div>

        <div v-if="loading" class="loading-section">
            <ProgressSpinner />
            <p class="mt-2 text-primary">Uploading CSV file...</p>
        </div>
    </div>
</template>

<style scoped>
.csv-upload-section {
    background: var(--dark-bg);
    padding: 20px;
    border-radius: 8px;
    border: 1px solid var(--border-light);
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.filter-item {
    display: flex;
    flex-direction: column;
    gap: 8px;
    margin-bottom: 20px;
}

.filter-label {
    font-weight: 600;
    color: var(--text-color);
    font-size: 14px;
    margin: 0;
    text-transform: uppercase;
    letter-spacing: 0.5px;
}

.filter-dropdown {
    width: 300px;
}

.upload-area {
    margin-bottom: 20px;
}

.upload-placeholder {
    text-align: center;
    padding: 40px 20px;
    color: var(--text-color);
}

.upload-placeholder i {
    color: var(--primary-blue);
}

.upload-placeholder p {
    margin: 0 0 8px 0;
    color: var(--text-color);
}

.upload-placeholder .text-sm {
    color: var(--text-muted);
}

.loading-section {
    text-align: center;
    padding: 20px;
}

.loading-section p {
    color: var(--primary-blue);
    margin: 8px 0 0 0;
}

@media (max-width: 768px) {
    .filter-dropdown {
        width: 100%;
    }

    .upload-placeholder {
        padding: 30px 15px;
    }
}
</style>
