<script	setup>
import ProtectedLayout from '@/components/ProtectedLayout.vue';
import TransactionDashboard from '../components/TransactionDashboard.vue';
import AppNavigation from '@/components/navigation.vue'
</script>

<template>
    <AppNavigation/>
    <ProtectedLayout>
    <div class="container mx-auto px-4">
        <h2 class="text-center my-4">Welcome to your Dashboard</h2>
        <p class="text-center mb-6">Here you can manage your transactions, view reports, and customize your settings.</p>

        <!-- Transaction Dashboard -->
        <TransactionDashboard />
    </div>
    </ProtectedLayout>
</template>
<script>
export default {
    name: 'AuthenticatedHomePage'
}
</script>
