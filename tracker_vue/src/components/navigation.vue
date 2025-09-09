<template>
  <Menubar :model="items">
    <template #end>
      <!-- Right side login/logout buttons -->
      <Button
        v-if="authStore.isAuthenticated"
        label="Logout"
        icon="pi pi-sign-out"
        class="p-button-outlined"
        @click="logout"
      />
      <Button
        v-else
        label="Login"
        icon="pi pi-sign-in"
        class="p-button-outlined"
        @click="router.push('/login')"
      />
    </template>
  </Menubar>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../store/auth.js'

// PrimeVue components
import Menubar from 'primevue/menubar'
import Button from 'primevue/button'

const authStore = useAuthStore()
const router = useRouter()

// Logout function
const logout = async () => {
  try {
    await authStore.logout(router)
  } catch (error) {
    console.error(error)
  }
}

// Menu items
const items = ref([
  {
    label: 'Home',
    icon: 'pi pi-home',
    command: () => router.push('/')
  },
  {
    label: 'Portfolio',
    icon: 'pi pi-chart-line',
    command: () => router.push('/portfolio')
  }
])
</script>
