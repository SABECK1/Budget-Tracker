<script setup>
import { useAuthStore } from '../store/auth.js'
import { onMounted } from 'vue'
import { useRouter } from 'vue-router'
import Button from 'primevue/button'

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

    <main class="layout-main">
      <div v-if="authStore.isLoading" class="loading-container">
          <div class="loading-spinner"></div>
          <p>Loading session...</p>
      </div>

      <template v-else>
          <div v-if="authStore.isAuthenticated">
              <slot />
          </div>
          <div v-else class="access-denied">
              <div class="access-denied-content">
                  <i class="pi pi-lock access-icon"></i>
                  <h2>Access Denied</h2>
                  <p>Please login to view this content.</p>
                  <Button 
                      label="Login Now"
                      icon="pi pi-sign-in"
                      class="p-button-lg"
                      @click="goToLogin"
                  />
              </div>
          </div>
      </template>
    </main>

    <AppFooter />
  </div>
</template>

<style scoped>
.layout-wrapper {
    display: flex;
    flex-direction: column;
    min-height: 100vh;
    background: var(--body-bg);
}

.layout-main {
    flex: 1;
    padding: 20px;
    background: var(--body-bg);
}

.loading-container {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    min-height: 200px;
    gap: 15px;
    color: var(--text-color);
}

.loading-spinner {
    width: 40px;
    height: 40px;
    border: 4px solid var(--border-light);
    border-top: 4px solid var(--primary-blue);
    border-radius: 50%;
    animation: spin 1s linear infinite;
}

@keyframes spin {
    0% { transform: rotate(0deg); }
    100% { transform: rotate(360deg); }
}

.access-denied {
    display: flex;
    align-items: center;
    justify-content: center;
    min-height: 60vh;
    padding: 20px;
}

.access-denied-content {
    text-align: center;
    max-width: 400px;
    padding: 40px;
    background: var(--dark-bg);
    border-radius: 12px;
    box-shadow: 0 10px 30px rgba(0, 0, 0, 0.5);
    border: 1px solid var(--border-dark);
}

.access-icon {
    font-size: 48px;
    color: var(--danger-red);
    margin-bottom: 20px;
    display: block;
}

.access-denied-content h2 {
    color: var(--text-color);
    margin: 0 0 10px 0;
    font-size: 28px;
    font-weight: 700;
}

.access-denied-content p {
    color: var(--text-muted);
    margin: 0 0 30px 0;
    font-size: 16px;
    line-height: 1.5;
}

:deep(.p-button) {
    border: none;
    border-radius: 6px;
    padding: 12px 24px;
    font-size: 16px;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    transition: all 0.2s ease;
}

:deep(.p-button:hover) {
    transform: translateY(-1px);
    box-shadow: 0 4px 12px rgba(0, 123, 255, 0.3);
}

:deep(.p-button:disabled) {
    background: var(--secondary-gray);
    cursor: not-allowed;
    transform: none;
    box-shadow: none;
}

@media (max-width: 768px) {
    .layout-main {
        padding: 15px;
    }
    
    .access-denied-content {
        padding: 30px 20px;
        max-width: 100%;
    }
    
    .access-icon {
        font-size: 36px;
    }
    
    .access-denied-content h2 {
        font-size: 24px;
    }
}
</style>
