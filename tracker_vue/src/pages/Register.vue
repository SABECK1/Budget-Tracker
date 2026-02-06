<template>
  <div class="register-container">
    <div class="register-card">
      <div class="register-header">
        <h2>Create Account</h2>
      </div>

      <form @submit.prevent="register" class="register-form">
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
          />
          <small v-if="emailError" class="p-error">{{ emailError }}</small>
        </div>

        <!-- Password Field -->
        <div class="field">
          <label for="password" class="form-label">Password</label>
          <Password 
            id="password" 
            v-model="password" 
            placeholder="Create a strong password"
            class="w-full"
            :class="{ 'p-invalid': passwordError }"
            :feedback="true"
            toggleMask
          />
          <small v-if="passwordError" class="p-error">{{ passwordError }}</small>
        </div>

        <!-- Password Confirmation Field -->
        <div class="field">
          <label for="passwordConfirm" class="form-label">Confirm Password</label>
          <Password 
            id="passwordConfirm" 
            v-model="passwordConfirm" 
            placeholder="Confirm your password"
            class="w-full"
            :class="{ 'p-invalid': confirmPasswordError }"
            toggleMask
          />
          <small v-if="confirmPasswordError" class="p-error">{{ confirmPasswordError }}</small>
        </div>

        <!-- Global Error Message -->
        <div v-if="error" class="error-message">
          <Message severity="error" :closable="false">{{ error }}</Message>
        </div>

        <!-- Success Message -->
        <div v-if="success" class="success-message">
          <Message severity="success" :closable="false">{{ success }}</Message>
        </div>

        <!-- Submit Button -->
        <Button 
          type="submit"
          label="Create Account"
          icon="pi pi-user-plus"
          class="w-full p-button-lg"
          :loading="isLoading"
          :disabled="!isValid"
        />

        <!-- Login Link -->
        <div class="login-link">
          Already have an account? 
          <router-link to="/login" class="login-link-text">
            Sign in here
          </router-link>
        </div>
      </form>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import Cookies from 'js-cookie'
import InputText from 'primevue/inputtext'
import Password from 'primevue/password'
import Button from 'primevue/button'
import Message from 'primevue/message'
import '../assets/css/main.css'

const router = useRouter()

const email = ref('')
const password = ref('')
const passwordConfirm = ref('')
const error = ref('')
const success = ref('')
const isLoading = ref(false)

const emailError = computed(() => {
    if (email.value && !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email.value)) {
        return 'Please enter a valid email address'
    }
    return null
})

const passwordError = computed(() => {
    if (password.value && password.value.length < 8) {
        return 'Password must be at least 8 characters long'
    }
    if (password.value && !/(?=.*[a-z])(?=.*[A-Z])(?=.*\d)/.test(password.value)) {
        return 'Password must contain at least one uppercase letter, one lowercase letter, and one number'
    }
    return null
})

const confirmPasswordError = computed(() => {
    if (passwordConfirm.value && password.value !== passwordConfirm.value) {
        return 'Passwords do not match'
    }
    return null
})

const isValid = computed(() => {
    return !emailError.value && !passwordError.value && !confirmPasswordError.value && 
           email.value && password.value && passwordConfirm.value && !isLoading.value
})

const register = async () => {
    if (!isValid.value) {
        error.value = 'Please check your information and try again'
        return
    }

    isLoading.value = true
    error.value = ''
    success.value = ''

    try {
        const response = await fetch(`${process.env.VUE_APP_API_BASE_URL}/register`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                "X-CSRFToken": Cookies.get('csrftoken'),
            },
            body: JSON.stringify({
                email: email.value,
                password: password.value
            }),
            credentials: "include"
        })

        const data = await response.json()

        if (response.ok) {
            success.value = "Registration successful! Redirecting to login..."
            isLoading.value = false

            setTimeout(() => {
                router.push("/login")
            }, 1500)
        } else {
            error.value = data.error || "Registration failed. Please try again."
            isLoading.value = false
        }
    } catch (err) {
        error.value = "An error occurred during registration. Please try again."
        isLoading.value = false
        console.error("Registration error:", err)
    }
}
</script>
<style>
.register-container {
    min-height: 100vh;
    display: flex;
    align-items: center;
    justify-content: center;
    background: var(--soothing-gradient);
    padding: 20px;
}

.register-card {
    background: var(--dark-bg);
    color: var(--text-color);
    padding: 40px;
    border-radius: 12px;
    box-shadow: 0 10px 30px rgba(0, 0, 0, 0.5);
    width: 100%;
    max-width: 400px;
    border: 1px solid var(--border-dark);
}

.register-header {
    text-align: center;
    margin-bottom: 30px;
}

.register-header h2 {
    margin: 0 0 10px 0;
    color: var(--text-color);
    font-size: 28px;
    font-weight: 700;
}

.register-header p {
    margin: 0;
    color: var(--text-muted);
    font-size: 14px;
}

.register-form {
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
    background: var(--white);
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

:deep(.p-password .p-password-panel .p-password-meter) {
    background: var(--border-light);
}

:deep(.p-password .p-password-panel .p-password-meter .p-password-strength.weak) {
    background: var(--danger-red);
}

:deep(.p-password .p-password-panel .p-password-meter .p-password-strength.medium) {
    background: var(--orange);
}

:deep(.p-password .p-password-panel .p-password-meter .p-password-strength.strong) {
    background: var(--success-green);
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
    background: var(--success-green);
    border: none;
    border-radius: 6px;
    padding: 12px 24px;
    font-size: 16px;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    transition: all 0.2s ease;
}

:deep(.p-button:hover:not(:disabled)) {
    background: #218838;
    transform: translateY(-1px);
    box-shadow: 0 4px 12px rgba(40, 167, 69, 0.3);
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

.success-message {
    margin-top: -10px;
}

:deep(.p-message-error) {
    background: var(--error-bg);
    border: 1px solid var(--error-border);
    color: #721c24;
    border-radius: 6px;
}

:deep(.p-message-success) {
    background: #d4edda;
    border: 1px solid #c3e6cb;
    color: #155724;
    border-radius: 6px;
}

.login-link {
    text-align: center;
    margin-top: 10px;
    color: var(--text-muted);
    font-size: 14px;
}

.login-link-text {
    color: var(--primary-blue);
    text-decoration: none;
    font-weight: 600;
    transition: color 0.2s ease;
}

.login-link-text:hover {
    color: #0056b3;
    text-decoration: underline;
}

@media (max-width: 480px) {
    .register-card {
        padding: 30px 20px;
        max-width: 100%;
    }
    
    .register-header h2 {
        font-size: 24px;
    }
}
</style>
