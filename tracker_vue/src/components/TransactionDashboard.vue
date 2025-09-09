<script setup>
import { ref, onMounted, computed } from "vue";
import DataTable from "primevue/datatable";
import Column from "primevue/column";
import Card from "primevue/card";
import FileUpload from 'primevue/fileupload';
import ProgressSpinner from 'primevue/progressspinner';
import axios from "axios";
import Cookies from 'js-cookie';

axios.defaults.xsrfCookieName = "csrftoken";
axios.defaults.xsrfHeaderName = "X-CSRFToken";
axios.defaults.withCredentials = true;

const baseurl = process.env.VUE_APP_API_BASE_URL;

// State
const transactions = ref([]);
const transactionSubtypes = ref([]);
const loading = ref(true);
const expandedRows = ref([]);
const editingTransaction = ref(null);
const editForm = ref({
    transaction_subtype: null,
    amount: '',
    note: '',
    isin: '',
    quantity: '',
    fee: '',
    tax: '',
    applyToAllWithSameNote: false
});

// Lazy loading state
const expandedData = ref(new Map()); // Cache for expanded row data
const expandedLoading = ref(new Set()); // Track which rows are loading

// CSV Upload state
const csvUploadResult = ref(null);
const csvUploading = ref(false);

// Fetch data on mount
onMounted(async () => {
    try {
        // Only load subtypes initially, not all transactions
        const subtypesRes = await axios.get(`${baseurl}/transactionsubtypes/`);
        transactionSubtypes.value = subtypesRes.data;

        // Load transaction counts by subtype for the summary table
        await loadTransactionCounts();
    } catch (err) {
        console.error("Error fetching data:", err);
    } finally {
        loading.value = false;
    }
});

// Load transaction counts for summary view
const loadTransactionCounts = async () => {
    try {
        const response = await axios.get(`${baseurl}/transactions/`);
        transactions.value = response.data;
    } catch (err) {
        console.error("Error loading transaction counts:", err);
    }
};

// Lazy load transactions for a specific subtype
const loadTransactionsForSubtype = async (subtypeId) => {
    if (expandedData.value.has(subtypeId)) {
        return expandedData.value.get(subtypeId);
    }

    expandedLoading.value.add(subtypeId);

    try {
        const response = await axios.get(`${baseurl}/transactions/?transaction_subtype=${subtypeId}`);
        const data = {
            transactions: response.data,
            pagination: {
                page: 1,
                limit: 50,
                total: response.data.length
            }
        };
        expandedData.value.set(subtypeId, data);
        return data;
    } catch (err) {
        console.error("Error loading transactions for subtype:", err);
        return { transactions: [], pagination: { page: 1, limit: 50, total: 0 } };
    } finally {
        expandedLoading.value.delete(subtypeId);
    }
};

// Handle row expansion
const onRowExpand = async (event) => {
    const subtypeId = event.data.subtype.id;
    await loadTransactionsForSubtype(subtypeId);
};

// Handle row collapse
const onRowCollapse = (event) => {
    // Optional: could clear cache here if memory is a concern
    // expandedData.value.delete(event.data.subtype.id);
};

// Computed properties for metrics
const totalTransactions = computed(() => transactions.value.length);

const totalAmount = computed(() => {
    return transactions.value.reduce((sum, t) => sum + parseFloat(t.amount || 0), 0);
});

const totalFees = computed(() => {
    return transactions.value.reduce((sum, t) => sum + parseFloat(t.fee || 0), 0);
});

const totalTaxes = computed(() => {
    return transactions.value.reduce((sum, t) => sum + parseFloat(t.tax || 0), 0);
});

// Get subtype object by ID
const getSubtypeById = (id) => {
    return transactionSubtypes.value.find(subtype => subtype.id === id);
};

// Group transactions by subtype
const transactionsBySubtype = computed(() => {
    const grouped = {};

    transactions.value.forEach(transaction => {
        const subtypeId = transaction.transaction_subtype;
        const subtypeObj = getSubtypeById(subtypeId);
        if (!subtypeObj) return;

        if (!grouped[subtypeId]) {
            grouped[subtypeId] = {
                subtype: subtypeObj,
                transactions: [],
                count: 0,
                totalAmount: 0,
                totalFees: 0,
                totalTaxes: 0
            };
        }

        grouped[subtypeId].transactions.push(transaction);
        grouped[subtypeId].count++;
        grouped[subtypeId].totalAmount += parseFloat(transaction.amount || 0);
        grouped[subtypeId].totalFees += parseFloat(transaction.fee || 0);
        grouped[subtypeId].totalTaxes += parseFloat(transaction.tax || 0);
    });

    return Object.values(grouped);
});

// Format currency
const formatCurrency = (amount) => {
    return new Intl.NumberFormat('en-US', {
        style: 'currency',
        currency: 'EUR'
    }).format(amount);
};

// Format date
const formatDate = (dateString) => {
    return new Date(dateString).toLocaleDateString();
};

// Edit functions
const startEdit = (transaction) => {
    editingTransaction.value = transaction.id;
    editForm.value = {
        transaction_subtype: transaction.transaction_subtype,
        amount: transaction.amount,
        note: transaction.note,
        isin: transaction.isin,
        quantity: transaction.quantity,
        fee: transaction.fee,
        tax: transaction.tax,
        applyToAllWithSameNote: false
    };
};

const cancelEdit = () => {
    editingTransaction.value = null;
    editForm.value = {
        transaction_subtype: null,
        amount: '',
        note: '',
        isin: '',
        quantity: '',
        fee: '',
        tax: '',
        applyToAllWithSameNote: false
    };
};

const saveEdit = async (transaction) => {
    try {
        // If applying to all with same note, do bulk update first
        if (editForm.value.applyToAllWithSameNote && editForm.value.note) {
            await axios.patch(`${baseurl}/transactions/bulk_update_by_note/`, {
                note: editForm.value.note,
                transaction_subtype: editForm.value.transaction_subtype
            }, {
                headers: {
                    'X-CSRFToken': Cookies.get('csrftoken'),
                },
                withCredentials: true,
            });
        }

        // Update the individual transaction
        const response = await axios.patch(`${baseurl}/transactions/${transaction.id}/`, {
            transaction_subtype: editForm.value.transaction_subtype,
            amount: editForm.value.amount,
            note: editForm.value.note,
            isin: editForm.value.isin,
            quantity: editForm.value.quantity,
            fee: editForm.value.fee,
            tax: editForm.value.tax
        }, {
            headers: {
                'X-CSRFToken': Cookies.get('csrftoken'),
            },
            withCredentials: true,
        });

        // Update the transaction in the local state
        const index = transactions.value.findIndex(t => t.id === transaction.id);
        if (index !== -1) {
            transactions.value[index] = response.data;
        }

        // Clear all cached data since bulk update may have affected multiple subtypes
        expandedData.value.clear();

        cancelEdit();

        // Refresh the data to update the grouped view
        const transactionsRes = await axios.get(`${baseurl}/transactions/`);
        transactions.value = transactionsRes.data;

    } catch (err) {
        console.error("Error updating transaction:", err);
        alert("Error updating transaction. Please try again.");
    }
};

// CSV Upload function
const onCsvUpload = async (event) => {
    const file = event.files[0];
    if (!file) return;

    csvUploading.value = true;
    csvUploadResult.value = null;

    const formData = new FormData();
    formData.append("file", file);

    try {
        const response = await axios.post(`${baseurl}/upload-csv/`, formData, {
            headers: {
                "Content-Type": "multipart/form-data",
                'X-CSRFToken': Cookies.get('csrftoken'),
            },
            credentials: 'include',
        });

        csvUploadResult.value = `Success: ${response.data.message || 'CSV uploaded successfully'}`;

        // Clear all cached expanded data since new transactions may have been added
        expandedData.value.clear();

        // Refresh transactions data after successful upload
        const transactionsRes = await axios.get(`${baseurl}/transactions/`);
        transactions.value = transactionsRes.data;

    } catch (error) {
        csvUploadResult.value = `Error: ${error.response ? error.response.data : error.message}`;
    } finally {
        csvUploading.value = false;
    }
};
</script>

<template>
    <div class="p-4">
        <h2 class="text-center mb-4">Transaction Dashboard</h2>

        <!-- Metrics Cards -->
        <div class="grid mb-4">
            <div class="col-12 md:col-3">
                <Card>
                    <template #title>Total Transactions</template>
                    <template #content>
                        <div class="text-3xl font-bold text-primary">{{ totalTransactions }}</div>
                    </template>
                </Card>
            </div>
            <div class="col-12 md:col-3">
                <Card>
                    <template #title>Total Amount</template>
                    <template #content>
                        <div class="text-3xl font-bold text-green-600">{{ formatCurrency(totalAmount) }}</div>
                    </template>
                </Card>
            </div>
            <div class="col-12 md:col-3">
                <Card>
                    <template #title>Total Fees</template>
                    <template #content>
                        <div class="text-3xl font-bold text-red-600">{{ formatCurrency(totalFees) }}</div>
                    </template>
                </Card>
            </div>
            <div class="col-12 md:col-3">
                <Card>
                    <template #title>Total Taxes</template>
                    <template #content>
                        <div class="text-3xl font-bold text-orange-600">{{ formatCurrency(totalTaxes) }}</div>
                    </template>
                </Card>
            </div>
        </div>

        <!-- Transactions by Subtype -->
        <Card class="mb-4">
            <template #title>Transactions by Subtype</template>
            <template #content>
                <DataTable
                    :value="transactionsBySubtype"
                    :loading="loading"
                    v-model:expandedRows="expandedRows"
                    dataKey="subtype.id"
                    tableStyle="min-width: 50rem"
                    stripedRows
                    showGridlines
                    @row-expand="onRowExpand"
                    @row-collapse="onRowCollapse"
                >
                    <Column field="subtype.name" header="Subtype" sortable />
                    <Column field="count" header="Transaction Count" sortable />
                    <Column field="totalAmount" header="Total Amount" sortable>
                        <template #body="slotProps">
                            {{ formatCurrency(slotProps.data.totalAmount) }}
                        </template>
                    </Column>
                    <Column field="totalFees" header="Total Fees" sortable>
                        <template #body="slotProps">
                            {{ formatCurrency(slotProps.data.totalFees) }}
                        </template>
                    </Column>
                    <Column field="totalTaxes" header="Total Taxes" sortable>
                        <template #body="slotProps">
                            {{ formatCurrency(slotProps.data.totalTaxes) }}
                        </template>
                    </Column>

                    <!-- Expandable row for individual transactions -->
                    <Column :expander="true" headerStyle="width: 3rem" />
                    <template #expansion="slotProps">
                        <div class="p-3">
                            <h5>Individual Transactions</h5>
                            <div v-if="expandedLoading.has(slotProps.data.subtype.id)" class="text-center p-4">
                                <ProgressSpinner />
                                <p class="mt-2 text-primary">Loading transactions...</p>
                            </div>
                            <DataTable
                                v-else
                                :value="expandedData.get(slotProps.data.subtype.id)?.transactions || []"
                                responsiveLayout="scroll"
                                :paginator="true"
                                :rows="50"
                                paginatorTemplate="FirstPageLink PrevPageLink PageLinks NextPageLink LastPageLink CurrentPageReport RowsPerPageDropdown"
                                :rowsPerPageOptions="[25, 50, 100]"
                                currentPageReportTemplate="Showing {first} to {last} of {totalRecords} transactions"
                            >
                                <Column field="created_at" header="Date" sortable>
                                    <template #body="slotProps">
                                        {{ formatDate(slotProps.data.created_at) }}
                                    </template>
                                </Column>
                                <Column header="Transaction Subtype">
                                    <template #body="slotProps">
                                        <select
                                            v-if="editingTransaction === slotProps.data.id"
                                            v-model="editForm.transaction_subtype"
                                            class="form-control"
                                        >
                                            <option
                                                v-for="subtype in transactionSubtypes"
                                                :key="subtype.id"
                                                :value="subtype.id"
                                            >
                                                {{ subtype.name }}
                                            </option>
                                        </select>
                                        <span v-else>{{ getSubtypeById(slotProps.data.transaction_subtype)?.name || 'Unknown' }}</span>
                                    </template>
                                </Column>
                                <Column field="amount" header="Amount" sortable>
                                    <template #body="slotProps">
                                        <input
                                            v-if="editingTransaction === slotProps.data.id"
                                            v-model="editForm.amount"
                                            type="number"
                                            step="0.01"
                                            class="form-control"
                                        />
                                        <span v-else>{{ formatCurrency(slotProps.data.amount) }}</span>
                                    </template>
                                </Column>
                                <Column field="note" header="Note">
                                    <template #body="slotProps">
                                        <input
                                            v-if="editingTransaction === slotProps.data.id"
                                            v-model="editForm.note"
                                            class="form-control"
                                        />
                                        <span v-else>{{ slotProps.data.note || '-' }}</span>
                                    </template>
                                </Column>
                                <Column field="isin" header="ISIN">
                                    <template #body="slotProps">
                                        <input
                                            v-if="editingTransaction === slotProps.data.id"
                                            v-model="editForm.isin"
                                            class="form-control"
                                        />
                                        <span v-else>{{ slotProps.data.isin || '-' }}</span>
                                    </template>
                                </Column>
                                <Column field="quantity" header="Quantity">
                                    <template #body="slotProps">
                                        <input
                                            v-if="editingTransaction === slotProps.data.id"
                                            v-model="editForm.quantity"
                                            type="number"
                                            step="0.01"
                                            class="form-control"
                                        />
                                        <span v-else>{{ slotProps.data.quantity || '-' }}</span>
                                    </template>
                                </Column>
                                <Column field="fee" header="Fee">
                                    <template #body="slotProps">
                                        <input
                                            v-if="editingTransaction === slotProps.data.id"
                                            v-model="editForm.fee"
                                            type="number"
                                            step="0.01"
                                            class="form-control"
                                        />
                                        <span v-else>{{ slotProps.data.fee ? formatCurrency(slotProps.data.fee) : '-' }}</span>
                                    </template>
                                </Column>
                                <Column field="tax" header="Tax">
                                    <template #body="slotProps">
                                        <input
                                            v-if="editingTransaction === slotProps.data.id"
                                            v-model="editForm.tax"
                                            type="number"
                                            step="0.01"
                                            class="form-control"
                                        />
                                        <span v-else>{{ slotProps.data.tax ? formatCurrency(slotProps.data.tax) : '-' }}</span>
                                    </template>
                                </Column>
                                <Column header="Actions">
                                    <template #body="slotProps">
                                        <div v-if="editingTransaction === slotProps.data.id">
                                            <div class="mb-2">
                                                <label>
                                                    <input
                                                        type="checkbox"
                                                        v-model="editForm.applyToAllWithSameNote"
                                                    />
                                                    Apply to all transactions with the same note
                                                </label>
                                            </div>
                                            <div class="d-flex gap-2">
                                                <button
                                                    @click="saveEdit(slotProps.data)"
                                                    class="btn btn-success btn-sm"
                                                >
                                                    Save
                                                </button>
                                                <button
                                                    @click="cancelEdit"
                                                    class="btn btn-secondary btn-sm"
                                                >
                                                    Cancel
                                                </button>
                                            </div>
                                        </div>
                                        <button
                                            v-else
                                            @click="startEdit(slotProps.data)"
                                            class="btn btn-primary btn-sm"
                                        >
                                            Edit
                                        </button>
                                    </template>
                                </Column>
                            </DataTable>
                        </div>
                    </template>
                </DataTable>
            </template>
        </Card>

        <!-- CSV Upload Section -->
        <Card class="mb-4">
            <template #title>Import Transactions</template>
            <template #content>
                <div class="p-4">
                    <FileUpload
                        name="file"
                        url="/api/upload-csv/"
                        accept=".csv"
                        :withCredentials="true"
                        :customUpload="true"
                        @uploader="onCsvUpload"
                        :disabled="csvUploading"
                        
                    >
                        <template #empty>
                            <div class="text-center p-4">
                                <i class="pi pi-upload text-4xl text-primary mb-3"></i>
                                <p class="text-lg">Drag and drop a CSV file here</p>
                                <p class="text-sm text-gray-600">Or click to browse and select a file</p>
                            </div>
                        </template>
                    </FileUpload>

                    <div v-if="csvUploading" class="text-center mb-3">
                        <ProgressSpinner />
                        <p class="mt-2 text-primary">Uploading CSV file...</p>
                    </div>

                    <div v-if="csvUploadResult && !csvUploading" class="mt-3">
                        <div
                            :class="csvUploadResult.startsWith('Success') ? 'bg-green-100 border-green-400 text-green-700' : 'bg-red-100 border-red-400 text-red-700'"
                            class="border-l-4 p-4 rounded"
                        >
                            <p class="font-semibold">{{ csvUploadResult.startsWith('Success') ? 'Success!' : 'Error!' }}</p>
                            <pre class="mt-2 whitespace-pre-wrap">{{ csvUploadResult }}</pre>
                        </div>
                    </div>
                </div>
            </template>
        </Card>
    </div>
</template>

<script>
export default {
    name: 'TransactionDashboard'
}
</script>

<style scoped>
.grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
    gap: 1rem;
}

.col-12 {
    grid-column: span 12;
}

@media (min-width: 768px) {
    .md\:col-3 {
        grid-column: span 3;
    }
}
</style>
