<script setup>
import { DataTable } from 'primevue';

</script>
<template>
<DataTable></DataTable>

</template>

<script>
import axios from 'axios';

const baseurl = process.env.VUE_APP_API_BASE_URL;

export default {
    name: 'TransactionTypeTable',
    mounted() {
        axios.get(`${baseurl}/transactiontypes/`)
            .then(response => {
                console.log(response.data);
            })
            .catch(error => {
                console.error(error);
            });
    }
}

</script>