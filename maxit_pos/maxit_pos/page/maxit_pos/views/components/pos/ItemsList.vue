<template>
    <VCard rounded="lg" class="ma-auto" min-height="700" flat>
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
        <!-- <v-list lines="two" max-height="500" class="overflow-y-auto">
          <v-list-item
            v-for="item in items"
            :key="item.order_id"
            class="border-b-sm"
          >
            <VRow>
              <VCol class="v-list-item__prepend justify-space-between">
                <div class="font-weight-bold">{{item.pickup_time}}</div>
                <v-avatar :color.once="get_random_color()">
                  <span class="text-h5">{{ get_intials(item.customer) }}</span>
                </v-avatar>
            </VCol>
              <VCol class="pl-0">
                <div class="v-list-item-title font-weight-semi-bold">{{ item.customer }}</div>
                <div class="v-list-item-subtitle">
                  <div>{{ item.email }}</div>
                  <div class="mt-1">{{ item.phone_no }}</div>
                </div>
              </VCol>
              <VCol class="v-list-item__append justify-end">
                <div class="font-weight-bold text-h7">
                  {{ '#'+item.order_id }}
                </div>
              </VCol>
            </VRow>
          </v-list-item>
        </v-list> -->
      </VCardText>
    </VCard>
</template>

<script setup>
    import {ref, watch} from "vue";
    import Item from "./Item.vue";
    import { usePosStore } from '../../../store/posStore';
    import {storeToRefs} from 'pinia';
    
    const posStore = usePosStore();
    const props = defineProps(['items']);
    const emit = defineEmits(['addItemToCart']);
    const {posProfileData, posFrm} = storeToRefs(posStore);
    const {update_cart} = posStore;

    const item_clicked = (item) => {
      update_cart({
        field: "qty",
        value: "+1",
        item: item
      });
    }
</script>