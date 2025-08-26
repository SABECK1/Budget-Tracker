<template>
  <div>
    <h2>Register</h2>

    <form @submit.prevent="register">
      <div>
        <label for="email">Email:</label>
        <input
          v-model="email"
          id="email"
          type="email"
          required
        />
      </div>

      <div>
        <label for="password">Password:</label>
        <input
          v-model="password"
          id="password"
          type="password"
          required
        />
      </div>

      <button type="submit">Register</button>
    </form>

    <p v-if="error">{{ error }}</p>
    <p v-if="success">{{ success }}</p>
  </div>
</template>

<script>
import { getCSRFToken } from '../store/auth'

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
  methods: {
    async register() {
      try {
        const response = await fetch(`${process.env.VUE_APP_API_BASE_URL}/api/register`, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            "X-CSRFToken": getCSRFToken()
          },
          body: JSON.stringify({
            email: this.email,
            password: this.password
          }),
          credentials: "include"
        })

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
