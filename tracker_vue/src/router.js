import { createRouter, createWebHistory } from 'vue-router'
import Home from './pages/HomePage.vue'
import Login from './pages/Login.vue'
import Register from './pages/Register.vue'
import Portfolio from './pages/Portfolio.vue'
import Accounts from './pages/Accounts.vue'
import Budgets from './pages/Budgets.vue'

const routes = [
  {
    path: '/',
    name: 'home',
    component: Home,
  },
  {
    path: '/login',
    name: 'login',
    component: Login,
  },
  {
    path: '/register',
    name: 'register',
    component: Register,
  },
  {
    path: '/portfolio',
    name: 'portfolio',
    component: Portfolio,
  },
  {
    path: '/accounts',
    name: 'accounts',
    component: Accounts,
  },
  {
    path: '/budgets',
    name: 'budgets',
    component: Budgets,
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

export default router
