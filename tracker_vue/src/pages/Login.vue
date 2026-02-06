<template>
  <div class="login-container">
    <div class="login-card">
      <div class="login-header">
        <h2>Welcome Back</h2>
      </div>

      <form @submit.prevent="login" class="login-form">
        <!-- Email Field -->
        <div class="field">
          <label for="email" class="form-label">Email Address</label>
          <InputText 
            id="email" 
            v-model="email" 
            type="email" 
            placeholder="Enter your email"
            class="w-full"
            :class="{ 'p-invalid': emailError }"
            @input="resetError"
          />
          <small v-if="emailError" class="p-error">{{ emailError }}</small>
        </div>

        <!-- Password Field -->
        <div class="field">
          <label for="password" class="form-label">Password</label>
          <Password 
            id="password" 
            v-model="password" 
            placeholder="Enter your password"
            class="w-full"
            :class="{ 'p-invalid': passwordError }"
            @input="resetError"
            toggleMask
          />
          <small v-if="passwordError" class="p-error">{{ passwordError }}</small>
        </div>

        <!-- Global Error Message -->
        <div v-if="error" class="error-message">
          <Message severity="error" :closable="false">{{ error }}</Message>
        </div>

        <!-- Submit Button -->
        <Button 
          type="submit"
          label="Sign In"
          icon="pi pi-sign-in"
          class="w-full p-button-lg"
          :loading="isLoading"
        />

        <!-- Sign Up Link -->
        <div class="signup-link">
          Don't have an account? 
          <router-link to="/register" class="signup-link-text">
            Sign up here
          </router-link>
        </div>
      </form>
    </div>
  </div>
</template>


<script setup>
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../store/auth'
import InputText from 'primevue/inputtext'
import Password from 'primevue/password'
import Button from 'primevue/button'
import Message from 'primevue/message'
import '../assets/css/main.css'

const authStore = useAuthStore()
const router = useRouter()

const email = ref('')
const password = ref('')
const error = ref('')
const isLoading = computed(() => authStore.isLoading)

const emailError = computed(() => {
    if (email.value && !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email.value)) {
        return 'Please enter a valid email address'
    }
    return null
})

const passwordError = computed(() => {
    if (password.value && password.value.length < 6) {
        return 'Password must be at least 6 characters'
    }
    return null
})

const isValid = computed(() => {
    return !emailError.value && !passwordError.value && email.value && password.value
})

const login = async () => {
    if (!isValid.value) {
        error.value = 'Please check your email and password'
        return
    }

    try {
        await authStore.login(email.value, password.value, router)
        if (!authStore.isAuthenticated) {
            error.value = "Login failed. Please check your credentials."
        }
    } catch (err) {
        error.value = "An error occurred during login. Please try again."
    }
}

const resetError = () => {
    error.value = ""
}
</script>
<style scoped>
.login-container {
    min-height: 100vh;
    display: flex;
    align-items: center;
    justify-content: center;
    background: var(--soothing-gradient);
    padding: 20px;
}

.login-card {
    background: var(--dark-bg);
    color: var(--text-color);
    padding: 40px;
    border-radius: 12px;
    box-shadow: 0 10px 30px rgba(0, 0, 0, 0.5);
    width: 100%;
    max-width: 400px;
    border: 1px solid var(--border-dark);
}

.login-header {
    text-align: center;
    margin-bottom: 30px;
}

.login-header h2 {
    margin: 0 0 10px 0;
    color: var(--text-color);
    font-size: 28px;
    font-weight: 700;
}

.login-header p {
    margin: 0;
    color: var(--text-muted);
    font-size: 14px;
}

.login-form {
    display: flex;
    flex-direction: column;
    gap: 20px;
}

.field {
    display: flex;
    flex-direction: column;
    gap: 8px;
}

.form-label {
    font-weight: 600;
    color: var(--text-color);
    font-size: 14px;
    margin: 0;
    text-transform: uppercase;
    letter-spacing: 0.5px;
}

:deep(.p-inputtext) {
    background: var(--true-black);
    border-radius: 6px;
    padding: 12px 16px;
    font-size: 16px;
    transition: all 0.2s ease;
}

:deep(.p-inputtext:focus) {
    outline: none;
    border-color: var(--primary-blue);
    box-shadow: 0 0 0 2px rgba(0, 123, 255, 0.25);
}

:deep(.p-password .p-inputtext) {
    border-radius: 6px;
    padding: 12px 16px;
    font-size: 16px;
}

:deep(.p-password .p-inputtext:focus) {
    outline: none;
    border-color: var(--primary-blue);
    box-shadow: 0 0 0 2px rgba(0, 123, 255, 0.25);
}

:deep(.p-password .p-password-panel) {
    background: var(--dark-bg);
    border: 1px solid var(--border-dark);
    color: var(--text-color);
}

:deep(.p-invalid) {
    border-color: var(--danger-red) !important;
    box-shadow: 0 0 0 2px rgba(220, 53, 69, 0.25) !important;
}

.p-error {
    color: var(--danger-red);
    font-size: 12px;
    margin-top: 4px;
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
    background: #0056b3;
    transform: translateY(-1px);
    box-shadow: 0 4px 12px rgba(0, 123, 255, 0.3);
}

:deep(.p-button:disabled) {
    background: var(--secondary-gray);
    cursor: not-allowed;
    transform: none;
    box-shadow: none;
}

.error-message {
    margin-top: -10px;
}

:deep(.p-message-error) {
    background: var(--error-bg);
    border: 1px solid var(--error-border);
    color: #721c24;
    border-radius: 6px;
}

.signup-link {
    text-align: center;
    margin-top: 10px;
    color: var(--text-muted);
    font-size: 14px;
}

.signup-link-text {
    color: var(--primary-blue);
    text-decoration: none;
    font-weight: 600;
    transition: color 0.2s ease;
}

.signup-link-text:hover {
    color: #0056b3;
    text-decoration: underline;
}

@media (max-width: 480px) {
    .login-card {
        padding: 30px 20px;
        max-width: 100%;
    }
    
    .login-header h2 {
        font-size: 24px;
    }
}
</style>
