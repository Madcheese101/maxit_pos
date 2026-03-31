<template>
    <!-- <v-app class="dashboard-container">
      <v-main>
      </v-main>
    </v-app> -->

  <VRow class="ma-10">
    <!-- Pick Ups -->
    <VCol md="4" lg="4" xs="12">
      <CardList listType="Pickups"/>
    </VCol>
    <!-- Late Pick Ups -->
    <VCol md="4" lg="4" xs="12">
      <CardList listType="Late Pickups"/>
    </VCol>
    <!-- Returns -->
    <VCol md="4" lg="4" xs="12">
      <CardList listType="Returns"/>
    </VCol>
    <!-- Late Returns -->
    <VCol md="4" lg="4" xs="12">
    <CardList listType="Late Returns"/>
    </VCol>
  </VRow>
</template>
  
<script setup>
  import CardList from './components/dashboard/CardList.vue';
// import { VRow } from 'vuetify/components';

</script>

<style scoped>
  .container1 {
    margin-top: 0px;
  }
</style>