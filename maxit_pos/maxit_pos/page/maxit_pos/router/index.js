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

const ROUTER_STATE_KEYS = ['back', 'current', 'forward', 'position', 'replaced', 'scroll']

const hasRouterState = (state) => {
  return Boolean(state) && ROUTER_STATE_KEYS.some((key) => state[key] !== undefined)
}

const preserveRouterHistoryState = () => {
  if (typeof window === 'undefined' || window.__maxitPosHistoryStatePatched) {
    return
  }

  const wrapHistoryMethod = (methodName) => {
    const originalMethod = window.history[methodName]

    window.history[methodName] = function patchedHistoryState(state, title, url) {
      const currentState = window.history.state

      if (!hasRouterState(currentState)) {
        return originalMethod.call(window.history, state, title, url)
      }

      if (state == null) {
        return originalMethod.call(window.history, { ...currentState }, title, url)
      }

      if (typeof state !== 'object') {
        return originalMethod.call(window.history, state, title, url)
      }

      const mergedState = { ...currentState, ...state }
      return originalMethod.call(window.history, mergedState, title, url)
    }
  }

  wrapHistoryMethod('replaceState')
  wrapHistoryMethod('pushState')
  window.__maxitPosHistoryStatePatched = true
}

preserveRouterHistoryState()

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