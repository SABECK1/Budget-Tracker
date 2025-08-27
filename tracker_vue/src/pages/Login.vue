<template>
    <section class="vh-100 gradient-custom">
    <div class="mask d-flex align-items-center h-100 gradient-custom-3">
      <div class="container h-100">
        <div class="row d-flex justify-content-center align-items-center h-100">
          <div class="col-12 col-md-9 col-lg-7 col-xl-6">
            <div class="card" style="border-radius: 15px;">
              <div class="card-body p-5">
                <h2 class="text-uppercase text-center mb-5">Login</h2>

                <!-- Vue login form -->
                <form @submit.prevent="login">
                  
                  <!-- Email -->
                  <div data-mdb-input-init class="form-outline mb-4">
                    <input 
                      v-model="email" 
                      id="email" 
                      type="email" 
                      placeholder="Email"
                      class="form-control form-control-lg" 
                      required 
                      @input="resetError"
                    />
                  </div>

                  <!-- Password -->
                  <div data-mdb-input-init class="form-outline mb-4">
                    <input 
                      v-model="password" 
                      id="password" 
                      type="password"
                      placeholder="Password"
                      class="form-control form-control-lg" 
                      required 
                      @input="resetError"
                    />
                  </div>

                  <!-- Submit -->
                  <div class="d-flex justify-content-center">
                    <button 
                      type="submit"
                      class="btn btn-success btn-block btn-lg gradient-custom-4 text-body"
                    >
                      Login
                    </button>
                  </div>

                  <!-- Error -->
                  <p v-if="error" class="text-center text-danger mt-3">{{ error }}</p>

                  <!-- Switch to register -->
                  <p class="text-center text-muted mt-5 mb-0">
                    Don't have an account?
                    <router-link to="/register" class="fw-bold text-body">
                      <u>Sign up!</u>
                    </router-link>
                  </p>

                </form>
                <!-- end Vue login form -->

              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
    </section>
</template>


<script>
import { useAuthStore } from '../store/auth'
import '../assets/css/main.css'
export default {
    name: "LoginPage",
    setup() {
        const authStore = useAuthStore()
        return {
            authStore
        }
    },
    data() {
        return {
            email: "",
            password: "",
            error: ""
        }
    },
    methods: {
        async login() {
            await this.authStore.login(this.email, this.password, this.$router)
            if (!this.authStore.isAuthenticated) {
                this.error = "Login failed. Please check your credentials."
            }
        },
        resetError() {
            this.error = ""
        }
    }
}
</script>
<style scoped>
.gradient-custom {
    background: linear-gradient(to top right, var(--blue), var(--red), var(--indigo));
}

.error {
    margin-top: 1rem;
}
</style>