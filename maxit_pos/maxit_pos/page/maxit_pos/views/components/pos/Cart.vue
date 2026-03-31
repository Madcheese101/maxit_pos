<template>
    <VCard rounded="lg" class="pa-3" min-height="75vh" flat>
        <div class="text-subtitle-1 mb-2">{{ __('Invoice Items') }}</div>

        <v-list class="cart-list" height="80vh">
            <v-list-item
                v-for="item in posCartItems"
                :key="item.idx"
                class="border-b"
            >
                <v-row align="center" density="compact">
                    <v-col cols="12" xl="4" align-self="center" align="start">
                        {{ item.item_name }}
                    </v-col>
                    <v-col cols="6" sm="3" xl="2" align-self="center" align="end">
                        <v-number-input
                            class="mt-2"
                            v-model="item.qty"
                            control-variant="hidden"
                            variant="outlined"
                            density="compact"
                            :precision="2"
                            label="Qty"
                            @change="update_number(item, 'qty', item.qty)"
                        />
                    </v-col>
                    <v-col cols="6" sm="3" xl="2" align-self="center" align="end">
                        <v-number-input
                            class="mt-2"
                            v-model="item.rate"
                            control-variant="hidden"
                            variant="outlined"
                            density="compact"
                            :precision="2"
                            :label="item.price_list_rate + ' ' + priceListCurrency"
                            @change="update_number(item, 'rate', item.rate)"
                        />
                    </v-col>
                    <v-col cols="8" sm="4" xl="2" align-self="center" align="end">
                        <v-number-input
                            class="mt-2"
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
                            class="mt-2"
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
                                    text="%"
                                />
                            </template>
                        </v-number-input>
                    </v-col>
                    <v-col class="text-right text-caption">
                        {{ item.amount }} {{ priceListCurrency }}
                    </v-col>
                    <v-col cols="3" sm="1" xl="1" align-self="center" align="end">
                        <v-btn
                            icon="mdi-delete"
                            variant="text"
                            @click="deleteItemFromCart(item)"
                        />
                    </v-col>
                </v-row>
            </v-list-item>
        </v-list>

        <v-divider class="my-3" />

        <div class="d-flex justify-space-between align-center">
            <div class="text-subtitle-1">{{ __('Total') }}</div>
            <div class="text-h6" v-html="frappe_.format(posFrm.doc.total, {'fieldtype': 'Currency'})"></div>
        </div>

        <v-btn color="deep-purple-accent-4" class="mt-3" block @click="emit('checkout')">
            {{ __('Checkout') }}
        </v-btn>
    </VCard>
</template>

<script setup>
    import { computed } from 'vue'
    import { usePosStore } from '../../../store/posStore';
    import {storeToRefs} from 'pinia';
    import { VCard } from 'vuetify/components';
    
    const __ = window.__;
    const frappe_ = frappe;
    // Initialize Store
    const posStore = usePosStore();
    // Get Refs from Store
    const {posFrm} = storeToRefs(posStore);
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

<style scoped>
    .cart-list {
        max-height: 44vh;
        overflow-y: auto;
    }
</style>