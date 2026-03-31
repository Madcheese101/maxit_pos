<template>
    <VCard rounded="lg" class="ma-auto" min-height="75vh" flat>
      <!-- Card Header -->
      <!-- List Section -->
      <VCardText>
        <v-row class="overflow-y-auto" style="max-height: 67vh">
          <v-col
            v-for="(item, idx) in props.items"
            :key="idx"
            xl="2"
            lg="3"
            md="6"
            sm="6"
            cols="6"
            min-height="50"
          >
            <Item :item="item" @click="item_clicked(item)"/>
          </v-col>
        </v-row>
      </VCardText>
    </VCard>
</template>

<script setup>
    import Item from "./Item.vue";
    import { usePosStore } from '../../../store/posStore';
    
    const posStore = usePosStore();
    const props = defineProps(['items']);
    const {update_cart} = posStore;

    const item_clicked = (item) => {
      update_cart({
        field: "qty",
        value: "+1",
        item: item
      });
    }
</script>