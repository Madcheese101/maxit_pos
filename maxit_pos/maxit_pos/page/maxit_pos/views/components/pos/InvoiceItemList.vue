<template>
  <v-data-table
    :items="posFrm ? posFrm.doc.items : []"
    :headers="headers"
    item-value="idx"
    class="elevation-1"
    v-model="selected"
    select-strategy="single"
    return-object
    :row-props="getRowProps"
    density="compact"
  >
    <template v-slot:item.item_name="{ item }">
      <span @click="rowClicked(item)">{{ item.item_name }}</span>
    </template>
    <template v-slot:item.uom="{ item }">
      <v-select 
        v-model="item.uom"
        :items="item.uoms"
        variant="outlined"
        density="compact"
        bg-color="white"
        flat
        @update:modelValue="val => update_text(item, 'uom', val)"
      />
    </template>

    <template v-slot:item.qty="{ item, index }">
      <v-text-field
        v-model="item.qty"
        type="number"
        variant="outlined"
        max-width="100"
        density="compact"
        hide-details
        @change="update_number(item, 'qty', item.qty, index)"
      />
    </template>

    <template v-slot:item.rate="{ item, index }">
      <v-text-field
        v-model="item.rate"
        type="number"
        variant="outlined"
        max-width="150"
        density="compact"
        hide-details
        :label="item.price_list_rate"
        @change="update_number(item, 'rate', item.rate, index)"
      />
    </template>

    <template v-slot:item.delete="{ item, index }">
      <v-btn
        icon="mdi-delete"
        variant="text"
        @click="delete_item(item)"
      ></v-btn>
    </template>
  </v-data-table>
</template>

<script setup>
    frappe.provide("log_");
    import { ref, watch } from "vue";
    import { usePosStore } from '../../../store/posStore';
    import { storeToRefs } from 'pinia';
    
    const headers = [
        { title: "Item", key: "item_name" },
        { title: "UOM", key: "uom", maxWidth: "100"},
        { title: "QTY", key: "qty", maxWidth: "100"},
        { title: "Rate", key: "rate", maxWidth: "150"},
        { title: "Amount", key: "amount", maxWidth: "200"},
        { title: "", key:"delete"}
    ];
    const selected = ref([]);
    const posStore = usePosStore();
    const {posProfileData, posFrm} = storeToRefs(posStore);
    const {update_cart, trigger_item_update} = posStore;
    
    const getRowProps = ({ item }) => {
      return {
        class: item.idx === selected.value[0]?.idx ? 'selected-row' : '',
      };
    };
    const rowClicked = async (item) => {
      if (item.idx === selected.value[0]?.idx){
        selected.value = [];
        return
      }
      selected.value = [item];
    }
    const update_text = async (item, field, value) => {
      update_cart({
          field: field,
          value: value,
          item: item,
      });
    }
    const update_number = async (item, field, value) => {
      // log_(index);
      update_cart({
          field: field,
          value: value,
          item: item,
          is_number: true
      });
    }

    const delete_item = async (item) => {
      log_("delete item", item);
    }
</script>

<style>
  .selected-row {
    background-color: #bdf6e6ff !important; /* Light teal, change as needed */
  }
  .v-table__wrapper > table > tbody > tr {
    background-color: #c6f4ffff !important;
    height: 50px !important;
  }
</style>