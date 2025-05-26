import { createRouter, createWebHistory, createMemoryHistory } from 'vue-router'
import Dashboard from '../views/Dashboard.vue'
import Customers from '../views/Customers.vue'
import Pos from '../views/Pos.vue'

const routes = [
  {
    path: '/app/maxit-pos/',
    name: 'POS',
    component: Pos,
    // props: true
  },
  // {
  //   path: '/app/maxit-pos/',
  //   name: 'Dashboard',
  //   component: Dashboard
  // },
  {
    path: '/app/maxit-pos/customers',
    name: 'Customers',
    component: Customers
  },
]

const router = createRouter({
    history: createWebHistory(),
    // abstract: createMemoryHistory(),
    routes: routes,
})

export default router