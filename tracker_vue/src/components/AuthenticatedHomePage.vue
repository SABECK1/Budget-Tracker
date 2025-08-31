<script	setup>
// import TransactionSubTypesTable from './TransactionSubTypesTable.vue';
import CSVUpload from './CSVUpload.vue';
</script>

<template>
    <h2 class="text-center my-4">Welcome to your Dashboard</h2>
    <p class="text-center">Here you can manage your transactions, view reports, and customize your settings.</p>
    
<c-s-v-upload></c-s-v-upload>
<!-- <TransactionSubTypesTable /> -->
</template>
<script>
export default {
    name: 'AuthenticatedHomePage'
}
</script>
