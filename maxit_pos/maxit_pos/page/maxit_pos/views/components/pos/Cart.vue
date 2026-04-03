<template>
    <VCard rounded="lg" class="pa-3" min-height="40vh" max-height="75vh" flat>
        <div class="text-subtitle-1 mb-2">{{ __('Invoice Items') }}</div>

        <div class="cart-scroll-container">
            <v-expansion-panels
                class="cart-panels"
                variant="accordion"
            >
                <v-expansion-panel
                    v-for="item in posCartItems"
                    :key="item.idx"
                    class="border-b"
                >
                <v-expansion-panel-title>
                    <v-row align="center" @click.stop dense>
                        <v-col cols="6" align="start" class="text-body-2 pa-0">
                            {{ item.idx }}. {{ item.item_name }}
                        </v-col>

                        <v-col cols="2" @click.stop>
                            <v-number-input
                                v-model="item.qty"
                                control-variant="hidden"
                                variant="outlined"
                                density="compact"
                                :precision="2"
                                label="Qty"
                                @change="update_number(item, 'qty', item.qty)"
                            />
                        </v-col>

                        <v-col cols="3">
                            <div class="text-body-2 pa-0" v-html="frappe_.format(item.amount, {'fieldtype': 'Currency'})"></div>
                        </v-col>

                        <v-col cols="1"  @click.stop>
                            <v-btn
                                icon="mdi-delete"
                                variant="text"
                                density="compact"
                                @click="deleteItemFromCart(item)"
                            />
                        </v-col>
                    </v-row>
                </v-expansion-panel-title>

                <v-expansion-panel-text>
                    <v-row dense>
                        <v-col cols="6" @click.stop>
                            <v-number-input
                                v-model="item.rate"
                                control-variant="hidden"
                                variant="outlined"
                                density="compact"
                                :disabled="!allow_rate_change"
                                :precision="2"
                                :label="__('Rate') + ': ' + item.price_list_rate + ' ' + priceListCurrency"
                                @change="update_number(item, 'rate', item.rate)"
                            />
                        </v-col>
                        <v-col cols="6" @click.stop>
                            <v-number-input
                                v-if="item.discount_type === 'Amount'"
                                v-model="item.discount_amount"
                                control-variant="hidden"
                                variant="outlined"
                                density="compact"
                                :precision="2"
                                :label="__('Discount')"
                                :disabled="!allow_discount_change"
                                @change="update_number(item, 'discount_amount', item.discount_amount)"
                            >
                                <template #append-inner>
                                    <v-btn
                                        size="small"
                                        variant="text"
                                        @click.stop="toggleDiscountType(item)"
                                    >
                                        {{ priceListCurrency }}
                                    </v-btn>
                                </template>
                            </v-number-input>

                            <v-number-input
                                v-if="item.discount_type === 'Percentage'"
                                v-model="item.discount_percentage"
                                control-variant="hidden"
                                variant="outlined"
                                density="compact"
                                :precision="2"
                                :label="__('Discount %')"
                                :disabled="!allow_discount_change"
                                @change="update_number(item, 'discount_percentage', item.discount_percentage)"
                            >
                                <template #append-inner>
                                    <v-btn
                                        size="small"
                                        variant="text"
                                        @click.stop="toggleDiscountType(item)"
                                        text="%"
                                    />
                                </template>
                            </v-number-input>
                        </v-col>
                    </v-row>
                </v-expansion-panel-text>
                </v-expansion-panel>
            </v-expansion-panels>
        </div>

        <v-divider class="my-3" />

        <div class="d-flex justify-space-between align-center">
            <div class="text-subtitle-1">{{ __('Total') }}</div>
            <div class="text-h6" v-html="frappe_.format(posFrm?.doc?.total, {'fieldtype': 'Currency'})"></div>
        </div>

        <v-btn color="green-lighten-1" class="mt-3" block @click="emit('checkout')">
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
    const posStore = usePosStore();
    const {posFrm, posProfileData} = storeToRefs(posStore);
    const {update_cart} = posStore;

    const emit = defineEmits(['checkout']);
    const posCartItems = computed(() => posFrm.value?.doc?.items || [])
    const priceListCurrency = computed(() => posFrm.value?.doc?.price_list_currency || "")
    const allow_discount_change = computed(() => posProfileData.value?.allow_discount_change)
    const allow_rate_change = computed(() => posProfileData.value?.allow_rate_change)
    
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
    .cart-scroll-container {
        height: 46.5vh;
        overflow-y: auto;
    }

    .cart-panels {
        background: transparent;
    }
</style>