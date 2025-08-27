<script setup>
import { useAuthStore } from '../store/auth.js'
import { onMounted } from 'vue'

// Import your components
import AppNavigation from '../components/navigation.vue'
import AppFooter from '../components/footer.vue'
import AuthenticatedHomePage from '@/components/AuthenticatedHomePage.vue'
import UnAuthenticatedHomePage from '@/components/UnAuthenticatedHomePage.vue'

const authStore = useAuthStore()


onMounted(async () => {
    await authStore.fetchUser()
})
</script>

<template>
    <AppNavigation />
    <div v-if="authStore.isAuthenticated">
        <AuthenticatedHomePage />
    </div>
    <p v-else>
        <UnAuthenticatedHomePage />
    </p>
    <AppFooter />
</template>