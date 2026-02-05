<script setup>
import { useAuthStore } from '../store/auth.js'
import { onMounted } from 'vue'
import { useRouter } from 'vue-router'

const authStore = useAuthStore()
const router = useRouter()

const goToLogin = () => {
    router.push('/login')
}

onMounted(async () => {
    // Only fetch if we haven't already
    if (!authStore.user) {
        await authStore.fetchUser()
    }
})
</script>

<template>
  <div class="layout-wrapper">
    <AppNavigation />

    <main>
      <div v-if="authStore.isLoading">
          <p>Loading session...</p>
      </div>

      <template v-else>
          <div v-if="authStore.isAuthenticated">
              <slot />
          </div>
          <div v-else class="access-denied">
              <h2>Access Denied</h2>
              <p>Please login to view this content.</p>
              <button @click="goToLogin">Login Now</button>
          </div>
      </template>
    </main>

    <AppFooter />
  </div>
</template>