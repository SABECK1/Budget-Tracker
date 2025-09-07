<script setup>
import { ref, onMounted, computed } from "vue";
import DataTable from "primevue/datatable";
import Column from "primevue/column";
import Card from "primevue/card";
import axios from "axios";

axios.defaults.xsrfCookieName = "csrftoken";
axios.defaults.xsrfHeaderName = "X-CSRFToken";
axios.defaults.withCredentials = true;

const baseurl = process.env.VUE_APP_API_BASE_URL;

// State
const transactions = ref([]);
const transactionSubtypes = ref([]);
const loading = ref(true);
const expandedRows = ref([]);

// Fetch data on mount
onMounted(async () => {
    try {
        const [transactionsRes, subtypesRes] = await Promise.all([
            axios.get(`${baseurl}/transactions/`),
            axios.get(`${baseurl}/transactionsubtypes/`)
        ]);

        transactions.value = transactionsRes.data;
        transactionSubtypes.value = subtypesRes.data;
    } catch (err) {
        console.error("Error fetching data:", err);
    } finally {
        loading.value = false;
    }
});

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

// Group transactions by subtype
const transactionsBySubtype = computed(() => {
    const grouped = {};

    transactions.value.forEach(transaction => {
        const subtype = transaction.transaction_subtype;
        const subtypeId = subtype.id;
        if (!grouped[subtypeId]) {
            grouped[subtypeId] = {
                subtype: subtype,
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
                            <DataTable :value="slotProps.data.transactions" responsiveLayout="scroll">
                                <Column field="created_at" header="Date" sortable>
                                    <template #body="slotProps">
                                        {{ formatDate(slotProps.data.created_at) }}
                                    </template>
                                </Column>
                                <Column field="amount" header="Amount" sortable>
                                    <template #body="slotProps">
                                        {{ formatCurrency(slotProps.data.amount) }}
                                    </template>
                                </Column>
                                <Column field="note" header="Note" />
                                <Column field="isin" header="ISIN" />
                                <Column field="quantity" header="Quantity" />
                                <Column field="fee" header="Fee">
                                    <template #body="slotProps">
                                        {{ slotProps.data.fee ? formatCurrency(slotProps.data.fee) : '-' }}
                                    </template>
                                </Column>
                                <Column field="tax" header="Tax">
                                    <template #body="slotProps">
                                        {{ slotProps.data.tax ? formatCurrency(slotProps.data.tax) : '-' }}
                                    </template>
                                </Column>
                            </DataTable>
                        </div>
                    </template>
                </DataTable>
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
