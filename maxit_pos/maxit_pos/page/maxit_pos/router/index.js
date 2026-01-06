import { createRouter, createWebHistory, createMemoryHistory } from 'vue-router'
import Dashboard from '../views/Dashboard.vue'
import Customers from '../views/Customers.vue'
import Pos from '../views/Pos.vue'

const routes = [
  {
    path: "/",
    // name: "POS",
    // component: Pos
    redirect: '/desk/maxit-pos/'
  },
  {
    path: '/desk/maxit-pos/',
    name: 'POS',
    component: Pos,
    // props: true
    // redirect: '/'
  },
  // {
  //   path: '/app/maxit-pos/',
  //   name: 'Dashboard',
  //   component: Dashboard
  // },
  {
    path: '/desk/maxit-pos/customers',
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