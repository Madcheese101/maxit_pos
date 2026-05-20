import { createRouter, createWebHistory, createMemoryHistory } from 'vue-router'
// import Dashboard from '../views/Dashboard.vue'
import Customers from '../views/Customers.vue'
import Orders from '../views/Orders.vue'
import Pos from '../views/Pos.vue'
import Items from '../views/Items.vue'
import Purchase from '../views/Purchase.vue'
import StockEntry from '../views/StockEntry.vue'
import CloseDay from '../views/CloseDay.vue'
import Expenses from '../views/Expenses.vue'

const expenseRoles = ['Expense User', 'Expense Manager']
const hasExpenseAccess = expenseRoles.some((role) => frappe.user.has_role(role))

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
  {
    path: '/desk/maxit-pos/orders',
    name: 'Orders',
    component: Orders
  },
  {
    path: '/desk/maxit-pos/items',
    name: 'Items',
    component: Items
  },
  {
    path: '/desk/maxit-pos/purchase',
    name: 'Purchase',
    component: Purchase
  },
  {
    path: '/desk/maxit-pos/stock-entry',
    name: 'StockEntry',
    component: StockEntry
  },
  {
    path: '/desk/maxit-pos/close-day',
    name: 'CloseDay',
    component: CloseDay
  },
  ...(hasExpenseAccess
    ? [{
        path: '/desk/maxit-pos/expenses',
        name: 'Expenses',
        component: Expenses
      }]
    : [])
]

const router = createRouter({
    history: createWebHistory(),
    // abstract: createMemoryHistory(),
    routes: routes,
})

export default router