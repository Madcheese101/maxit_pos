<template>
    <v-app class="pos-view-container">
      <v-main class="ma-10">
        <!-- <Navbar></Navbar> -->
         <!-- Toolbar -->
        <v-toolbar border color="white">
          <!-- right section -->
          <!-- <v-btn icon="mdi-menu"></v-btn> -->
          <v-toolbar-title :text="pos_profile"></v-toolbar-title>

          <!-- left section -->
          <v-menu>
            <template v-slot:activator="{ props }">
              <v-btn icon="mdi-dots-vertical" variant="text" v-bind="props"></v-btn>
            </template>
            <v-list>
              <!-- <v-list-item v-for="(item, i) in items" :key="i" value="i" title="Return Invoice"/> -->
              <v-list-item title="Full Screen" @click="console.log('Full Screen')"/>
              <v-list-item title="Return Invoice" @click="console.log('return invoice')"/>
              <v-list-item title="Print Last Invoice" @click="console.log('print invoice')"/>
            </v-list>
          </v-menu>
          <v-btn icon="mdi-logout" variant="text"/>
        </v-toolbar>
        <v-row class="columns-container mt-5">
          <v-col class="right-section" cols="6">
            <FiltersSection :customFilters="posProfileData.custom_filters"/>
            <ItemsList/>
          </v-col>
        </v-row>
      </v-main>
    </v-app>
  </template>
  
<script setup>
  //   import Navbar from '../components/navbar.vue';
  // TO-DO
  // const propss = defineProps(['appDefaults']);
  import FiltersSection from './components/pos/FiltersSection.vue';
  import ItemsList from './components/pos/ItemsList.vue';
  import { usePosStore } from '../store/posStore';
  import { storeToRefs } from 'pinia';
  import { ref } from 'vue';

  const posStore = usePosStore();
  const {posProfileData, pos_profile} = storeToRefs(posStore);
</script>
  
<style scoped>
  .container1 {
    margin-top: 0px;
  }
  .pos-view-container{
    background: #edf2f5;
  }

  .hover-button:hover {
    /* background-color: #6b3fe7; */
    /* color: white !important; */
    /* color: #6b3fe7; */
  }
</style>