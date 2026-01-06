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
            <FiltersSection :customFilters="posProfileData.custom_filters" 
              :allowedItemGroups="posProfileData.item_groups"
              @getItems="get_items"/>
            <ItemsList :items="items" @addItemToCart="update_cart"/>
          </v-col>

          <v-col class="left-section" cols="6">
            <!-- <FiltersSection :customFilters="posProfileData.custom_filters" 
              :allowedItemGroups="posProfileData.item_groups"
              @getItems="get_items"/> -->
            <!-- <InvoiceItemList v-if="cart_items.length > 0" :items="cart_items"/> -->
            <InvoiceItemList :items_uoms="items_uoms"/>
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
  import InvoiceItemList from './components/pos/InvoiceItemList.vue';
  import { usePosStore } from '../store/posStore';
  import { storeToRefs } from 'pinia';
  import { ref, watch} from 'vue';

  const items = ref([]);
  const items_uoms = ref([]);
  const posStore = usePosStore();
  const {posProfileData, pos_profile, posFrm} = storeToRefs(posStore);
  const {make_new_invoice, add_item_to_invoice} = posStore;

  const get_items = (filters) => {
    search_term = filters ? filters.search_term : "";
    item_group = filters ? filters.item_group : null;
    custom_filters = filters ? filters.filters : [];

    frappe.call("maxit_pos.maxit_pos.page.maxit_pos.api.api.get_items", {
        pos_profile_data: posProfileData.value,
        search_term: search_term,
        item_group: item_group,
        custom_filters: custom_filters
    }).then((res) => {
        items.value = res.message[0];
        items_uoms.value = res.message[1];
        // make_new_invoice();
    })
  }
  get_items();

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