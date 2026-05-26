<template>
    <v-navigation-drawer
        :location="isAppRTL() ? 'right' : 'left'"
        rail
        mobile-breakpoint="xs"
      >
        <v-list>
            <v-list-item
            v-if="user"
            class="user-profile-item"
            >
              <div class="d-flex align-center user-profile-row">
                <v-avatar color="blue-grey-lighten-4" size="36">
                  <v-img v-if="user.avatar" :src="user.avatar" :alt="user.full_name"></v-img>
                  <span v-else class="text-caption font-weight-bold">{{ userInitials }}</span>
                </v-avatar>
                <div class="ms-2 user-meta">
                  <div class="text-body-2 font-weight-medium text-truncate">{{ user.full_name }}</div>
                  <div class="text-caption text-medium-emphasis text-truncate">{{ user.email }}</div>
                </div>
              </div>
            </v-list-item>
        </v-list>

        <v-divider class="border-opacity-100"></v-divider>

        <v-list density="compact" nav>
          <!-- <v-list-item prepend-icon="mdi-view-dashboard" title="Dashboard" value="dashboard" to="/app/maxit-pos/"></v-list-item> -->
          <v-list-item prepend-icon="mdi-cash-register" title="POS" color="#6b3fe7" value="pos" to="/desk/maxit-pos/"></v-list-item>
          <v-list-item prepend-icon="mdi-account-multiple" title="Customers" color="#6b3fe7" value="customers" to="/desk/maxit-pos/customers"></v-list-item>
          <v-list-item prepend-icon="mdi-clipboard-text-clock" title="Orders" value="orders" to="/desk/maxit-pos/orders" v-if="props.showPosProfileDependent"></v-list-item>
          <v-list-item prepend-icon="mdi-cart" title="Purchase" value="purchase" to="/desk/maxit-pos/purchase" v-if="purchaseEnabled"></v-list-item>
          <v-list-item prepend-icon="mdi-swap-horizontal-bold" title="Stock Entry" value="stock-entry" to="/desk/maxit-pos/stock-entry"></v-list-item>
          <v-list-item prepend-icon="mdi-cash-minus" title="Expenses" value="expenses" to="/desk/maxit-pos/expenses" v-if="expensesEnabled"></v-list-item>
          <v-list-item prepend-icon="mdi-cash-lock" title="Close Day" value="close-day" to="/desk/maxit-pos/close-day" v-if="closeDayEnabled"></v-list-item>
          <v-list-item prepend-icon="mdi-package" title="Items" value="items" to="/desk/maxit-pos/items" v-if="props.showPosProfileDependent"></v-list-item>
        </v-list>

        <template #append>
          <v-divider class="border-opacity-100"></v-divider>
          <v-list density="compact" nav class="pb-2">
            <v-list-item
              v-if="pos_opening"
              prepend-icon="mdi-door-closed-lock"
              :title="__('Close Shift')"
              value="close-shift"
              @click="closeShift"
            ></v-list-item>
            <v-list-item
              prepend-icon="mdi-logout"
              title="Logout"
              value="logout"
              @click="logout"
            ></v-list-item>
          </v-list>
        </template>
    </v-navigation-drawer>
</template>

<script setup>
    import { computed } from 'vue';
  import { storeToRefs } from 'pinia';
  import { usePosStore } from '../../store/posStore';

  const __ = window.__;

  const props = defineProps(['showPosProfileDependent']);
  const posStore = usePosStore();
  const { pos_opening, posProfileData } = storeToRefs(posStore);
  const { close_pos, isAppRTL } = posStore;
  const purchaseEnabled = computed(() => {
      const roles = ['Purchase User', 'Purchase Manager', 'Administrator', 'System Manager'];
      return roles.some(role => frappe.user.has_role(role)) && posProfileData.value?.allow_purchase;
  });
    const expensesEnabled = computed(() => {
      const roles = ['Expense User', 'Expense Manager'];
      return roles.some(role => frappe.user.has_role(role));
    });
  const closeDayEnabled = computed(() => {
      const roles = ['Accounts User', 'Accounts Manager', 'Administrator', 'System Manager'];
      return roles.some(role => frappe.user.has_role(role));
  });
  const user = computed(() => {
    const fullName = frappe.user.full_name ? frappe.user.full_name() : frappe.user.name;
    const avatar = frappe.user.image ? frappe.user.image() : '';
    const email = frappe.user.name || '';

    return {
      full_name: fullName,
      avatar,
      email,
    };
  });

  const userInitials = computed(() => {
    const names = (user.value.full_name || '').trim().split(/\s+/).filter(Boolean);
    if (!names.length) return 'U';
    if (names.length === 1) return names[0].slice(0, 2).toUpperCase();
    return `${names[0][0]}${names[names.length - 1][0]}`.toUpperCase();
  });

  const logout = async () => {
    try {
      // await frappe.logout();
      await frappe.app.logout();
    } catch (error) {
      window.location.href = '/login';
    }
  };

  const closeShift = () => {
    frappe.confirm(
      __('Are you sure you want to close this shift?'),
      async () => {
        await close_pos();
      },
      () => {}
    );
  };
</script>

<style scoped>
  .user-profile-item {
    padding-inline: 8px !important;
  }

  .user-profile-row {
    width: 100%;
    min-width: 0;
  }

  .user-meta {
    min-width: 0;
  }
</style>