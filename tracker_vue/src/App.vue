<script setup>
import { onMounted } from 'vue';
import { RouterView } from 'vue-router';
import Toast from 'primevue/toast';

onMounted(async () => {
  try {
    await fetch(`${process.env.VUE_APP_API_BASE_URL}/set-csrf-token`, {
      credentials: "include"
    });
    console.log("CSRF cookie initialized");
  } catch (err) {
    console.error("Failed to initialize CSRF cookie:", err);
  }
});
</script>

<template>
  <RouterView />
  <Toast />
</template>