<script setup>
import { ref, onMounted } from "vue";
import DataTable from "primevue/datatable";
import Column from "primevue/column";
import axios from "axios";

axios.defaults.xsrfCookieName = "csrftoken";
axios.defaults.xsrfHeaderName = "X-CSRFToken";
axios.defaults.withCredentials = true;

const baseurl = process.env.VUE_APP_API_BASE_URL;

// state
const transactionTypes = ref([]);
const expandedRows = ref({});

// fetch both transactiontypes + subtypes
onMounted(async () => {
    try {
        const [typesRes, subtypesRes] = await Promise.all([
            axios.get(`${baseurl}/transactiontypes/`),
            axios.get(`${baseurl}/transactionsubtypes/`)
        ]);

        const subtypesByType = {};
        subtypesRes.data.forEach((st) => {
            // transaction_type is a URL like ".../transactiontypes/1/"
            const match = st.transaction_type.match(/\/(\d+)\/?$/);
            const typeId = match ? parseInt(match[1], 10) : null;

            if (typeId) {
                if (!subtypesByType[typeId]) subtypesByType[typeId] = [];
                subtypesByType[typeId].push(st);
            }
        });

        // attach subtypes to each type
        transactionTypes.value = typesRes.data.map((t) => ({
            ...t,
            subtypes: subtypesByType[t.id] || []
        }));
    } catch (err) {
        console.error(err);
    }
});
</script>

<template>
    <DataTable v-model:expandedRows="expandedRows" :value="transactionTypes" dataKey="id" tableStyle="min-width: 50rem">
        <!-- expansion column -->
        <Column expander style="width: 3rem" />

        <!-- main transaction type columns -->
        <Column field="name" header="Name" sortable />
        <Column field="description" header="Description" />

        <!-- expanded content -->
        <template #expansion="slotProps">
            <div class="p-3">
                <h4 class="mb-3">Subtypes for {{ slotProps.data.name }}</h4>
                <DataTable :value="slotProps.data.subtypes" responsiveLayout="scroll">
                    <Column field="name" header="Subtype Name" />
                    <Column field="description" header="Description" />
                </DataTable>
            </div>
        </template>
    </DataTable>
</template>
