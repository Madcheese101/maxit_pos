<template>
    <VCard rounded="lg" class="ma-auto" min-height="70vh" max-height="70vh" width="100%" flat>
        <!-- Card Header -->
        <!-- List Section -->
        <v-list lines="one" class="overflow-y-auto" max-height="70vh">
            <div v-for="item in posItems"  :key="item.code">
                <v-list-item :activatable="false" :title="item.item_code + ' (' + item.qty + ')'" >
                    <template v-slot:append>
                        <v-btn v-if="item.qty > 1"
                        color="red-lighten-3"
                        icon="mdi-minus"
                        variant="text"
                        @click="decreaseQty(item)"
                        ></v-btn>
                        <v-btn
                        color="red-lighten-1"
                        icon="mdi-delete"
                        variant="text"
                        @click="deleteItemFromCart(item)"
                        ></v-btn>
                    </template>
                </v-list-item>
                <v-divider class="ma-0"></v-divider>
            </div>
        </v-list>
        <!-- {{ reactiveTotal }} -->
    </VCard>
</template>

<script setup>
    import { computed, ref, watch } from 'vue'
    import { usePosStore } from '../../../../store/posStore';
    import {storeToRefs} from 'pinia';
    // Initialize Store
    const posStore = usePosStore();
    // Get Refs from Store
    const {posFrm,reactiveTotal} = storeToRefs(posStore);
    const {update_cart} = posStore;
    const posItems = computed(() => posFrm.value?.doc?.items || [])

    const decreaseQty = async (item) => {
        if (item.qty > 1){
            update_cart({
                field: 'qty',
                value: `${item.qty - 1}`,
                item: item,
                is_number: true
            });
        } else {
            deleteItemFromCart(item);
        }
    }

    const deleteItemFromCart = async (item) => {
        const index = posFrm.value.doc.items.indexOf(item);
        if (index !== -1) {
            posFrm.value.doc.items.splice(index, 1);
            posFrm.value.refresh_field('items');
            await posFrm.value.script_manager.trigger("calculate_taxes_and_totals");
        }
    }
</script>