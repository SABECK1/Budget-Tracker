<script setup>
import { ref, onMounted, computed, watch, nextTick } from "vue";
import DataTable from "primevue/datatable";
import Column from "primevue/column";
import Card from "primevue/card";
import FileUpload from 'primevue/fileupload';
import ProgressSpinner from 'primevue/progressspinner';
import InputText from "primevue/inputtext";
import InputNumber from "primevue/inputnumber";
import Dropdown from "primevue/dropdown";
import Button from "primevue/button";
import Toast from 'primevue/toast';
import { useToast } from 'primevue/usetoast';
import Chart from 'primevue/chart'
import axios from "axios";
import Cookies from 'js-cookie';

axios.defaults.xsrfCookieName = "csrftoken";
axios.defaults.xsrfHeaderName = "X-CSRFToken";
axios.defaults.withCredentials = true;

const baseurl = process.env.VUE_APP_API_BASE_URL;

const toast = useToast();

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

// Filter state
const noteFilter = ref('');
const subtypeFilter = ref(null);

// Add transaction state
const addForm = ref({
    transaction_subtype: null,
    amount: '',
    note: '',
    isin: '',
    quantity: '',
    fee: '',
    tax: ''
});

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

// Watch for filter changes to clear cache and reset expanded state
watch([noteFilter, subtypeFilter], async () => {
    // Clear expanded cache when filters change
    expandedData.value.clear();

    // Reset expanded rows after DOM updates to avoid conflicts
    await nextTick(() => {
        expandedRows.value = [];
    });
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

// Lazy load transactions for a specific subtype with filtering
const loadTransactionsForSubtype = async (subtypeId) => {
    if (expandedData.value.has(subtypeId)) {
        const cachedData = expandedData.value.get(subtypeId);
        // Check if filters have changed and we need to refilter
        if (cachedData.noteFilter !== noteFilter.value || cachedData.subtypeFilter !== subtypeFilter.value) {
            // Filters changed, need to refetch and filter
            expandedData.value.delete(subtypeId);
        } else {
            return cachedData;
        }
    }

    expandedLoading.value.add(subtypeId);

    try {
        const response = await axios.get(`${baseurl}/transactions/?transaction_subtype=${subtypeId}`);
        let filteredTransactions = response.data;

        // Apply filters to the expanded transactions if any filters are active
        if (noteFilter.value || subtypeFilter.value) {
            filteredTransactions = filterTransactions(filteredTransactions);

            // Apply note filter across all transactions if subtype filter allows this subtype
            if (noteFilter.value) {
                filteredTransactions = filteredTransactions.filter(t =>
                    t.note && t.note.toLowerCase().includes(noteFilter.value.toLowerCase())
                );
            }
        }

        const data = {
            transactions: filteredTransactions,
            pagination: {
                page: 1,
                limit: 50,
                total: filteredTransactions.length
            },
            noteFilter: noteFilter.value, // Cache filter state
            subtypeFilter: subtypeFilter.value
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

// Group transactions by subtype (with filtering)
const transactionsBySubtype = computed(() => {
    // First, filter transactions based on current filters
    const filteredTransactions = filterTransactions(transactions.value);

    const grouped = {};

    filteredTransactions.forEach(transaction => {
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

// Pie chart computed properties
const incomeChartData = computed(() => {
    const incomeSubtypes = transactionSubtypes.value.filter(subtype =>
        subtype.transaction_type_name === 'Income'
    );
    console.log(incomeSubtypes);

    const labels = [];
    const data = [];
    const colors = [
        '#FF6384', '#36A2EB', '#FFCE56', '#4BC0C0', '#9966FF', '#FF9F40', '#FF6384', '#C9CBCF'
    ];

    incomeSubtypes.forEach(subtype => {
        const subtypeTransactions = transactions.value.filter(t => t.transaction_subtype === subtype.id);
        const totalAmount = Math.abs(subtypeTransactions.reduce((sum, t) => sum + parseFloat(t.amount || 0), 0));

        if (totalAmount > 0) {
            labels.push(subtype.name);
            data.push(totalAmount);
        }
    });

    return {
        labels,
        datasets: [{
            data,
            backgroundColor: colors.slice(0, labels.length),
            borderWidth: 1
        }]
    };
});

const expenseChartData = computed(() => {
    const expenseSubtypes = transactionSubtypes.value.filter(subtype =>
        subtype.transaction_type_name === 'Expense'
    );

    const labels = [];
    const data = [];
    const colors = [
        '#FF6384', '#36A2EB', '#FFCE56', '#4BC0C0', '#9966FF', '#FF9F40', '#FF6384', '#C9CBCF'
    ];

    expenseSubtypes.forEach(subtype => {
        const subtypeTransactions = transactions.value.filter(t => t.transaction_subtype === subtype.id);
        const totalAmount = Math.abs(subtypeTransactions.reduce((sum, t) => sum + parseFloat(t.amount || 0), 0));

        if (totalAmount > 0) {
            labels.push(subtype.name);
            data.push(totalAmount);
        }
    });

    return {
        labels,
        datasets: [{
            data,
            backgroundColor: colors.slice(0, labels.length),
            borderWidth: 1
        }]
    };
});

const savingsChartData = computed(() => {
    const savingsSubtypes = transactionSubtypes.value.filter(subtype =>
        subtype.transaction_type_name === 'Savings'
    );

    const labels = [];
    const data = [];
    const colors = [
        '#FF6384', '#36A2EB', '#FFCE56', '#4BC0C0', '#9966FF', '#FF9F40', '#FF6384', '#C9CBCF'
    ];

    savingsSubtypes.forEach(subtype => {
        const subtypeTransactions = transactions.value.filter(t => t.transaction_subtype === subtype.id);
        const totalAmount = Math.abs(subtypeTransactions.reduce((sum, t) => sum + parseFloat(t.amount || 0), 0));

        if (totalAmount > 0) {
            labels.push(subtype.name);
            data.push(totalAmount);
        }
    });
    console.log(labels, data);
    return {
        labels,
        datasets: [{
            data,
            backgroundColor: colors.slice(0, labels.length),
            borderWidth: 1
        }]
    };
});

const chartOptions = {
    responsive: true,
    plugins: {
        legend: {
            position: 'right'
        },
        tooltip: {
            callbacks: {
                label: function (context) {
                    return `${context.label}: €${context.parsed.toFixed(2)}`;
                }
            }
        }
    }
};

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
        // If applying to all with same note/ISIN, do bulk update first
        if (editForm.value.applyToAllWithSameNote) {
            const isStock = editForm.value.isin && editForm.value.isin.trim() !== '';
            if (isStock && editForm.value.isin) {
                // For stock transactions, update by ISIN
                await axios.patch(`${baseurl}/transactions/bulk_update_by_isin/`, {
                    isin: editForm.value.isin,
                    is_buy: transaction.amount > 0,
                    transaction_subtype: editForm.value.transaction_subtype
                }, {
                    headers: {
                        'X-CSRFToken': Cookies.get('csrftoken'),
                    },
                    withCredentials: true,
                });
            } else if (editForm.value.note) {
                // For regular transactions, update by note
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
        toast.add({ severity: 'error', summary: 'Error', detail: 'Error updating transaction. Please try again.', life: 5000 });
    }
};

// Delete function
const deleteTransaction = async (transaction) => {
    if (!confirm('Are you sure you want to delete this transaction? This action cannot be undone.')) {
        return;
    }

    try {
        await axios.delete(`${baseurl}/transactions/${transaction.id}/`, {
            headers: {
                'X-CSRFToken': Cookies.get('csrftoken'),
            },
            withCredentials: true,
        });

        // Clear all cached data since deletion may have affected other subtypes
        expandedData.value.clear();

        // Refresh the data to update the grouped view
        const transactionsRes = await axios.get(`${baseurl}/transactions/`);
        transactions.value = transactionsRes.data;

        toast.add({ severity: 'success', summary: 'Success', detail: 'Transaction deleted successfully.', life: 3000 });
    } catch (err) {
        console.error("Error deleting transaction:", err);
        toast.add({ severity: 'error', summary: 'Error', detail: 'Error deleting transaction. Please try again.', life: 5000 });
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

// Filter functions
const clearFilters = () => {
    noteFilter.value = '';
    subtypeFilter.value = null;
};

// Helper: Filter transactions based on current filters
const filterTransactions = (transactionsList) => {
    return transactionsList.filter(transaction => {
        const matchesNote = !noteFilter.value ||
            (transaction.note && transaction.note.toLowerCase().includes(noteFilter.value.toLowerCase()));

        const matchesSubtype = !subtypeFilter.value ||
            transaction.transaction_subtype === subtypeFilter.value;

        return matchesNote && matchesSubtype;
    });
};

// Add transaction function
const addTransaction = async () => {
    if (!addForm.value.transaction_subtype || !addForm.value.amount) {
        toast.add({ severity: 'error', summary: 'Validation Error', detail: 'Transaction Type and Amount are required.', life: 5000 });
        return;
    }

    try {
        await axios.post(`${baseurl}/transactions/`, addForm.value, {
            headers: {
                'X-CSRFToken': Cookies.get('csrftoken'),
            },
            withCredentials: true,
        });

        // Clear form
        addForm.value = {
            transaction_subtype: null,
            amount: '',
            note: '',
            isin: '',
            quantity: '',
            fee: '',
            tax: ''
        };

        // Refresh data
        await loadTransactionCounts();
        expandedData.value.clear();

        toast.add({ severity: 'success', summary: 'Success', detail: 'Transaction added successfully.', life: 3000 });
    } catch (err) {
        console.error("Error adding transaction:", err.toJSON());
        toast.add({ severity: 'error', summary: 'Error', detail: 'Error adding transaction. Please try again.', life: 5000 });
    }
};
</script>

<template>
    <div class="p-4">
        <h2 class="text-center mb-4">Transaction Dashboard</h2>

        <!-- Metrics Cards -->
        <div class="metrics-cards mb-4">
            <div class="insight-card">
                <h3>Total Transactions</h3>
                <p class="text-primary">{{ totalTransactions }}</p>
            </div>
            <div class="insight-card">
                <h3>Total Amount</h3>
                <p class="text-green-600">{{ formatCurrency(totalAmount) }}</p>
            </div>
            <div class="insight-card">
                <h3>Total Fees</h3>
                <p class="text-red-600">{{ formatCurrency(totalFees) }}</p>
            </div>
            <div class="insight-card">
                <h3>Total Taxes</h3>
                <p class="text-orange-600">{{ formatCurrency(totalTaxes) }}</p>
            </div>
        </div>

        <!-- Pie Charts for Category Breakdown -->
        <div class="charts-section mb-4">
            <div class="chart-row">
                <!-- Income Chart -->
                <Card class="chart-card">
                    <template #title>Income Breakdown</template>
                    <template #content>
                        <div class="chart-container" v-if="incomeChartData.datasets[0].data.length > 0">
                            <Chart type="pie" :data="incomeChartData" :options="chartOptions" />
                        </div>
                        <div class="no-data" v-else>
                            <p class="text-center text-muted">No income data available</p>
                        </div>
                    </template>
                </Card>

                <!-- Expense Chart -->
                <Card class="chart-card">
                    <template #title>Expense Breakdown</template>
                    <template #content>
                        <div class="chart-container" v-if="expenseChartData.datasets[0].data.length > 0">
                            <Chart type="pie" :data="expenseChartData" :options="chartOptions" />
                        </div>
                        <div class="no-data" v-else>
                            <p class="text-center text-muted">No expense data available</p>
                        </div>
                    </template>
                </Card>

                <!-- Savings (Investment) Chart -->
                <Card class="chart-card">
                    <template #title>Investment Breakdown</template>
                    <template #content>
                        <div class="chart-container" v-if="savingsChartData.datasets[0].data.length > 0">
                            <Chart type="pie" :data="savingsChartData" :options="chartOptions" />
                        </div>
                        <div class="no-data" v-else>
                            <p class="text-center text-muted">No investment data available</p>
                        </div>
                    </template>
                </Card>
            </div>
        </div>

        <!-- Global Filters -->
        <div class="filter-section mb-4">
            <div class="filter-controls">
                <div class="filter-item">
                    <label for="note-filter" class="filter-label">Search Notes:</label>
                    <InputText id="note-filter" v-model="noteFilter" placeholder="Search transaction notes..."
                        class="filter-input" />
                </div>
                <div class="filter-item">
                    <label for="subtype-filter" class="filter-label">Filter by Type:</label>
                    <Dropdown id="subtype-filter" v-model="subtypeFilter" :options="transactionSubtypes"
                        option-label="name" option-value="id" placeholder="All types" show-clear
                        class="filter-dropdown" />
                </div>
                <div class="filter-item">
                    <Button label="Clear Filters" icon="pi pi-times" class="p-button-secondary p-button-sm"
                        @click="clearFilters" />
                </div>
            </div>
        </div>

        <!-- Transactions by Subtype -->
        <Card class="mb-4">
            <template #title>Transactions by Subtype</template>
            <template #content>
                <DataTable :value="transactionsBySubtype" :loading="loading" v-model:expandedRows="expandedRows"
                    dataKey="subtype.id" tableStyle="min-width: 50rem" stripedRows showGridlines
                    @row-expand="onRowExpand" @row-collapse="onRowCollapse">
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
                            <DataTable v-else :value="expandedData.get(slotProps.data.subtype.id)?.transactions || []"
                                responsiveLayout="scroll" :paginator="true" :rows="50"
                                paginatorTemplate="FirstPageLink PrevPageLink PageLinks NextPageLink LastPageLink CurrentPageReport RowsPerPageDropdown"
                                :rowsPerPageOptions="[25, 50, 100]"
                                currentPageReportTemplate="Showing {first} to {last} of {totalRecords} transactions">
                                <Column field="created_at" header="Date" sortable>
                                    <template #body="slotProps">
                                        {{ formatDate(slotProps.data.created_at) }}
                                    </template>
                                </Column>
                                <Column header="Transaction Subtype">
                                    <template #body="slotProps">
                                        <select v-if="editingTransaction === slotProps.data.id"
                                            v-model="editForm.transaction_subtype" class="form-control">
                                            <option v-for="subtype in transactionSubtypes" :key="subtype.id"
                                                :value="subtype.id">
                                                {{ subtype.name }}
                                            </option>
                                        </select>
                                        <span v-else>{{ getSubtypeById(slotProps.data.transaction_subtype)?.name ||
                                            'Unknown' }}</span>
                                    </template>
                                </Column>
                                <Column field="amount" header="Amount" sortable>
                                    <template #body="slotProps">
                                        <input v-if="editingTransaction === slotProps.data.id" v-model="editForm.amount"
                                            type="number" step="0.01" class="form-control" />
                                        <span v-else>{{ formatCurrency(slotProps.data.amount) }}</span>
                                    </template>
                                </Column>
                                <Column field="note" header="Note">
                                    <template #body="slotProps">
                                        <input v-if="editingTransaction === slotProps.data.id" v-model="editForm.note"
                                            class="form-control" />
                                        <span v-else>{{ slotProps.data.note || '-' }}</span>
                                    </template>
                                </Column>
                                <Column field="isin" header="ISIN">
                                    <template #body="slotProps">
                                        <input v-if="editingTransaction === slotProps.data.id" v-model="editForm.isin"
                                            class="form-control" />
                                        <span v-else>{{ slotProps.data.isin || '-' }}</span>
                                    </template>
                                </Column>
                                <Column field="quantity" header="Quantity">
                                    <template #body="slotProps">
                                        <input v-if="editingTransaction === slotProps.data.id"
                                            v-model="editForm.quantity" type="number" step="0.01"
                                            class="form-control" />
                                        <span v-else>{{ slotProps.data.quantity || '-' }}</span>
                                    </template>
                                </Column>
                                <Column field="fee" header="Fee">
                                    <template #body="slotProps">
                                        <input v-if="editingTransaction === slotProps.data.id" v-model="editForm.fee"
                                            type="number" step="0.01" class="form-control" />
                                        <span v-else>{{ slotProps.data.fee ? formatCurrency(slotProps.data.fee) : '-'
                                            }}</span>
                                    </template>
                                </Column>
                                <Column field="tax" header="Tax">
                                    <template #body="slotProps">
                                        <input v-if="editingTransaction === slotProps.data.id" v-model="editForm.tax"
                                            type="number" step="0.01" class="form-control" />
                                        <span v-else>{{ slotProps.data.tax ? formatCurrency(slotProps.data.tax) : '-'
                                            }}</span>
                                    </template>
                                </Column>
                                <Column header="Actions">
                                    <template #body="slotProps">
                                        <div v-if="editingTransaction === slotProps.data.id">
                                            <div class="mb-2">
                                                <label>
                                                    <input type="checkbox" v-model="editForm.applyToAllWithSameNote" />
                                                    Assign subtype to all transactions with the same {{ editForm.isin ?
                                                        'ISIN' : 'note' }}
                                                </label>
                                            </div>
                                            <div class="d-flex gap-2">
                                                <button @click="saveEdit(slotProps.data)"
                                                    class="btn btn-success btn-sm">
                                                    Save
                                                </button>
                                                <button @click="cancelEdit" class="btn btn-secondary btn-sm">
                                                    Cancel
                                                </button>
                                            </div>
                                        </div>
                                        <div v-else class="d-flex gap-2">
                                            <button @click="startEdit(slotProps.data)" class="btn btn-primary btn-sm">
                                                Edit
                                            </button>
                                            <button @click="deleteTransaction(slotProps.data)"
                                                class="btn btn-danger btn-sm">
                                                Delete
                                            </button>
                                        </div>
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
                    <FileUpload name="file" url="/api/upload-csv/" accept=".csv" :withCredentials="true"
                        :customUpload="true" @uploader="onCsvUpload" :disabled="csvUploading">
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
                        <div :class="csvUploadResult.startsWith('Success') ? 'bg-green-100 border-green-400 text-green-700' : 'bg-red-100 border-red-400 text-red-700'"
                            class="border-l-4 p-4 rounded">
                            <p class="font-semibold">{{ csvUploadResult.startsWith('Success') ? 'Success!' : 'Error!' }}
                            </p>
                            <pre class="mt-2 whitespace-pre-wrap">{{ csvUploadResult }}</pre>
                        </div>
                    </div>
                </div>
            </template>
        </Card>

        <!-- Add Transaction Form -->
        <Card class="mb-4">
            <template #title>Add Transaction Manually</template>
            <template #content>
                <div class="p-fluid form-grid">
                    <div class="field">
                        <label for="add-transaction_subtype" class="form-label">Transaction Type *</label>
                        <Dropdown id="add-transaction_subtype" v-model="addForm.transaction_subtype"
                            :options="transactionSubtypes" option-label="name" option-value="id"
                            placeholder="Select transaction type" class="w-full" />
                    </div>
                    <div class="field">
                        <label for="add-amount" class="form-label">Amount *</label>
                        <InputNumber id="add-amount" v-model="addForm.amount" mode="decimal" :minFractionDigits="2"
                            class="w-full" />
                    </div>
                    <div class="field">
                        <label for="add-note" class="form-label">Note</label>
                        <InputText id="add-note" v-model="addForm.note" placeholder="Optional note" class="w-full" />
                    </div>
                    <div class="field">
                        <label for="add-isin" class="form-label">ISIN</label>
                        <InputText id="add-isin" v-model="addForm.isin" placeholder="Optional ISIN" class="w-full" />
                    </div>
                    <div class="field">
                        <label for="add-tax" class="form-label">Tax</label>
                        <InputNumber id="add-tax" v-model="addForm.tax" mode="decimal" :minFractionDigits="2"
                            class="w-full" />
                    </div>
                    <div class="field">
                        <label for="add-quantity" class="form-label">Quantity</label>
                        <InputNumber id="add-quantity" v-model="addForm.quantity" mode="decimal" :minFractionDigits="2"
                            class="w-full" />
                    </div>
                    <div class="field">
                        <label for="add-fee" class="form-label">Fee</label>
                        <InputNumber id="add-fee" v-model="addForm.fee" mode="decimal" :minFractionDigits="2"
                            class="w-full" />
                    </div>
                    <div class="field col-span-full">
                        <Button label="Add Transaction" icon="pi pi-plus" @click="addTransaction"
                            class="p-button-success" />
                    </div>
                </div>
            </template>
        </Card>
        <Toast />
    </div>
</template>

<script>
export default {
    name: 'TransactionDashboard'
}
</script>

<style scoped>
.metrics-cards {
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
}

.filter-section {
    background: #f8f9fa;
    padding: 20px;
    border-radius: 8px;
    border: 1px solid #dee2e6;
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.filter-controls {
    display: flex;
    gap: 20px;
    align-items: flex-end;
    flex-wrap: wrap;
}

.filter-item {
    display: flex;
    flex-direction: column;
    gap: 8px;
}

.filter-item:last-child {
    margin-left: auto;
}

.filter-label {
    font-weight: 600;
    color: #495057;
    font-size: 14px;
    margin: 0;
    text-transform: uppercase;
    letter-spacing: 0.5px;
}

.filter-input {
    width: 250px;
    padding: 8px 12px;
    border: 1px solid #ced4da;
    border-radius: 4px;
    font-size: 14px;
    background: #ffffff;
}

.filter-input:focus {
    outline: none;
    border-color: #007bff;
    box-shadow: 0 0 0 2px rgba(0, 123, 255, 0.25);
}

.filter-dropdown {
    width: 200px;
}

.form-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
    gap: 20px;
}

.field {
    display: flex;
    flex-direction: column;
}

.field.col-span-full {
    grid-column: 1 / -1;
}

.form-label {
    font-weight: 600;
    color: #495057;
    font-size: 14px;
    margin: 0 0 4px 0;
    text-transform: uppercase;
    letter-spacing: 0.5px;
}

.charts-section {
    background: #ffffff;
    border-radius: 8px;
    border: 1px solid #e9ecef;
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
}

.chart-row {
    display: flex;
    gap: 20px;
    flex-wrap: wrap;
}

.chart-card {
    flex: 1;
    min-width: 300px;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.chart-container {
    height: 300px;
    display: flex;
    align-items: center;
    justify-content: center;
    padding: 20px;
}

.no-data {
    height: 300px;
    display: flex;
    align-items: center;
    justify-content: center;
    padding: 20px;
}

.no-data p {
    color: #6c757d;
    font-style: italic;
    margin: 0;
}

@media (max-width: 768px) {
    .filter-controls {
        flex-direction: column;
        align-items: stretch;
        gap: 15px;
    }

    .filter-item:last-child {
        margin-left: 0;
    }

    .filter-input {
        width: 100%;
    }

    .filter-dropdown {
        width: 100%;
    }

    .chart-row {
        flex-direction: column;
        gap: 15px;
    }

    .chart-card {
        min-width: unset;
    }
}
</style>
