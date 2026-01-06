<template>
    <v-navigation-drawer
        rail
        mobile-breakpoint="xs"
      >
        <v-list>
          <v-list-item
            prepend-avatar="https://randomuser.me/api/portraits/women/85.jpg"
            subtitle="sandra_a88@gmailcom"
            title="Sandra Adams"
          ></v-list-item>
        </v-list>

        <v-divider class="border-opacity-100"></v-divider>

        <v-list density="compact" nav>
          <!-- <v-list-item prepend-icon="mdi-view-dashboard" title="Dashboard" value="dashboard" to="/app/maxit-pos/"></v-list-item> -->
          <v-list-item prepend-icon="mdi-store" title="POS" color="#6b3fe7" value="pos" to="/desk/maxit-pos/"></v-list-item>
          <v-list-item prepend-icon="mdi-account-multiple" title="Customers" color="#6b3fe7" value="customers" to="/desk/maxit-pos/customers"></v-list-item>
        </v-list>
    </v-navigation-drawer>
</template>