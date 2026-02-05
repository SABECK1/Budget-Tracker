
import PrimeVue from 'primevue/config';
import Aura from '@primeuix/themes/aura';
import { createApp } from 'vue'
import { createPinia } from 'pinia'
import router from './router'
import App from './App.vue'
import { useAuthStore } from './store/auth'
import { definePreset } from '@primeuix/themes';
import 'primeicons/primeicons.css';
import { ToastService } from 'primevue';

const pinia = createPinia()

const app = createApp(App);

const stylePreset = definePreset(Aura, {
    semantic: {
        primary: {
            50: '{green.50}',
            100: '{green.100}',
            200: '{green.200}',
            300: '{green.300}',
            400: '{green.400}',
            500: '{green.500}',
            600: '{green.600}',
            700: '{green.700}',
            800: '{green.800}',
            900: '{green.900}',
            950: '{green.950}'
        },
        colorScheme: {
            dark: {
                surface: {
                    0: '#ffffff',
                    50: '{neutral.50}',
                    100: '{neutral.100}',
                    200: '{neutral.200}',
                    300: '{neutral.300}',
                    400: '{neutral.400}',
                    500: '{neutral.500}',
                    600: '{neutral.600}',
                    700: '{neutral.700}',
                    800: '{neutral.800}',
                    900: '{neutral.900}',
                    950: '{neutral.950}'
                }
            }
        }
    }
});

app.use(PrimeVue, {
    theme: {
        preset: stylePreset,
        // options: {
        //     darkModeSelector: '.app-dark'
        // }
    }
});

app.use(pinia)
app.use(ToastService)
app.use(router)

const authStore = useAuthStore(pinia)
authStore.setCsrfToken()

app.mount('#app')