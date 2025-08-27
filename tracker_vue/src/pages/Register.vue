<template>
  <section class="vh-100 gradient-custom">
    <div class="mask d-flex align-items-center h-100 gradient-custom-3">
      <div class="container h-100">
        <div class="row d-flex justify-content-center align-items-center h-100">
          <div class="col-12 col-md-9 col-lg-7 col-xl-6">
            <div class="card" style="border-radius: 15px;">
              <div class="card-body p-5">
                <h2 class="text-uppercase text-center mb-5">Create an account</h2>

                <!-- Vue form -->
                <form @submit.prevent="register">
                  <div data-mdb-input-init class="form-outline mb-4">
                    <input v-model="email" type="email" id="email" class="form-control form-control-lg" required placeholder="Email"/>
                  </div>

                  <div data-mdb-input-init class="form-outline mb-4">
                    <input v-model="password" type="password" id="password" class="form-control form-control-lg"
                      required placeholder="Password"/>
                  </div>

                  <div data-mdb-input-init class="form-outline mb-4">
                    <input v-model="passwordConfirm" type="password" id="passwordConfirm"
                      class="form-control form-control-lg" required placeholder="Repeat Password" />
                  </div>

                  <p class="text-center text-danger mt-2" v-if="password && passwordConfirm && !passwordMatch">
                    Passwords do not match
                  </p>

                  <div class="d-flex justify-content-center">
                    <button type="submit" class="btn btn-success btn-block btn-lg gradient-custom-4 text-body">
                      Register
                    </button>
                  </div>

                  <!-- Vue feedback -->
                  <p class="text-center text-danger mt-3" v-if="error">{{ error }}</p>
                  <p class="text-center text-success mt-3" v-if="success">{{ success }}</p>

                  <p class="text-center text-muted mt-5 mb-0">
                    Already have an account?
                    <router-link to="/login" class="fw-bold text-body">
                      <u>Login here</u></router-link>
                  </p>

                </form>
                <!-- end Vue form -->

              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </section>
</template>

<script>
import Cookies from 'js-cookie';

export default {
  name: "RegisterPage",
  data() {
    return {
      email: "",
      password: "",
      error: "",
      success: ""
    }
  },

  computed: {
    passwordMatch() {
      return this.password === this.passwordConfirm;
    }
  },

  methods: {
    async register() {
      try {
        const response = await fetch(`${process.env.VUE_APP_API_BASE_URL}/register`, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            "X-CSRFToken": Cookies.get('csrftoken'),
          },
          body: JSON.stringify({
            email: this.email,
            password: this.password
          }),
          credentials: "include"
        })
        console.log(response)

        const data = await response.json()

        if (response.ok) {
          this.success = "Registration successful! Please log in."
          this.error = ""

          setTimeout(() => {
            this.$router.push("/login")
          }, 1000)
        } else {
          this.error = data.error || "Registration failed"
          this.success = ""
        }
      } catch (err) {
        this.error = "An error occurred during registration: " + err
        this.success = ""
      }
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