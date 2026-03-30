<template>
    <VCard rounded="lg" class="ma-auto" min-height="70vh" width="90%" flat>
        <v-row>
            <!-- Items Col -->
            <v-col>
                <v-list>
                    <v-list-item
                        v-for="item in posCartItems"
                        :key="item.idx"
                        class="border-b"
                    >
                        <v-row align="center" density="compact">
                            <!-- Item Name -->
                            <v-col cols="4" align-self="center" fill-height align="start">
                                {{ item.item_name }}
                            </v-col>
                            <!-- QTY Input -->
                            <v-col align-self="center" align="end">
                                <v-number-input
                                class="mt-3"
                                v-model="item.qty"
                                control-variant="hidden"
                                variant="outlined"
                                density="compact"
                                :precision="2"
                                label="Qty"
                                @change="update_number(item, 'qty', item.qty)"
                                />
                            </v-col>
                            <!-- Rate Input -->
                            <v-col align-self="center" align="end">
                                <v-number-input
                                class="mt-3"
                                v-model="item.rate"
                                control-variant="hidden"
                                variant="outlined"
                                density="compact"
                                :precision="2"
                                :label="item.price_list_rate + ' ' + priceListCurrency"
                                @change="update_number(item, 'rate', item.rate)"
                                />
                            </v-col>
                            <!-- Discount Input + Single Toggle Button -->
                            <v-col align-self="center" align="end">
                                <v-number-input
                                    class="mt-3"
                                    v-if="item.discount_type === 'Amount'"
                                    v-model="item.discount_amount"
                                    control-variant="hidden"
                                    variant="outlined"
                                    density="compact"
                                    :precision="2"
                                    label="Discount"
                                    @change="update_number(item, 'discount_amount', item.discount_amount)"
                                >
                                    <template #append-inner>
                                        <v-btn
                                            size="small"
                                            variant="text"
                                            @click="toggleDiscountType(item)"
                                            >
                                            {{ priceListCurrency }}
                                        </v-btn>
                                    </template>
                                </v-number-input>
                                <v-number-input
                                    class="mt-3"
                                    v-if="item.discount_type === 'Percentage'"
                                    v-model="item.discount_percentage"
                                    control-variant="hidden"
                                    variant="outlined"
                                    density="compact"
                                    :precision="2"
                                    label="Discount %"
                                    @change="update_number(item, 'discount_percentage', item.discount_percentage)"
                                    >
                                        <template #append-inner>
                                            <v-btn
                                                size="small"
                                                variant="text"
                                                @click="toggleDiscountType(item)"
                                                text="%"/>
                                        </template>
                                </v-number-input>
                            </v-col>
                            <!-- Amount Display -->
                            <v-col align-self="center" fill-height align="end">
                                {{ item.amount }} {{ priceListCurrency }}
                            </v-col>
                            <!-- Delete Button -->
                            <v-col cols="1" align-self="center" class="text-right" align="end">
                                <v-btn
                                icon="mdi-delete"
                                variant="text"
                                @click="deleteItemFromCart(item)"
                                />
                            </v-col>
                        </v-row>
                    </v-list-item>
                </v-list>
            </v-col>
            <!-- Totals Col -->
            <v-col cols="4">
                <v-row>
                    <!-- Labels Col -->
                    <v-col>
                        <div class="text-h6">{{__("Total")}}</div>
                    </v-col>
                    <!-- Values Col -->
                    <v-col>
                        <div class="text-center">
                            <div class="text-h5" v-html="frappe_.format(posFrm.doc.total, {'fieldtype': 'Currency'})"></div>
                        </div>
                    </v-col>
                </v-row>
                <v-btn color="deep-purple-accent-4" class="ma-4" large block @click="emit('checkout')">{{__("Checkout")}}</v-btn>
            </v-col>
        </v-row>
        
        <!-- {{ reactiveTotal }} -->
    </VCard>
</template>

<script setup>
    import { computed, ref, watch } from 'vue'
    import { usePosStore } from '../../../store/posStore';
    import {storeToRefs} from 'pinia';
    import { VCard } from 'vuetify/components';
    
    const __ = window.__;
    const frappe_ = frappe;
    const headers = [
        { title: "Item", key: "item_name" },
        { title: "Rate", key: "rate", maxWidth: "150"},
        { title: "", key:"delete"}
    ];
    // Initialize Store
    const posStore = usePosStore();
    // Get Refs from Store
    const {posFrm, reactiveTotal} = storeToRefs(posStore);
    const {update_cart} = posStore;
    // ---
    const emit = defineEmits(['checkout']);
    const posCartItems = computed(() => posFrm.value?.doc?.items || [])
    const priceListCurrency = computed(() => posFrm.value?.doc?.price_list_currency || "")

    const update_number = async (item, field, value) => {
        update_cart({
            field: field,
            value: value,
            item: item,
            is_number: true
        });
    }

    const deleteItemFromCart = async (item) => {
        const index = posFrm.value.doc.items.indexOf(item);
        if (index === -1) {
            return;
        }
        posFrm.value.doc.items.splice(index, 1);
        posFrm.value.refresh_field('items');
        await posFrm.value.script_manager.trigger("calculate_taxes_and_totals");
        posFrm.value.trigger('refresh_totals');
    }
    function toggleDiscountType(item) {
        item.discount_type =
        item.discount_type === 'Percentage' ? 'Amount' : 'Percentage'
    }
</script>