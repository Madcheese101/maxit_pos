<template>
    <VCard rounded="xl" class="cart-card pa-3" flat>
        <div class="cart-scroll-container">
            <v-data-table
                v-model:expanded="expanded"
                :headers="cartHeaders"
                :items="posCartItems"
                :items-per-page="cartItemsPerPage"
                item-value="idx"
                density="compact"
                hide-default-footer
                hide-default-header
                expand-on-click
                class="cart-table"
            >
                <template #item.item_name="{ item }">
                    <div class="cart-item-name">
                        {{ item.idx }}. {{ item.item_name }}
                    </div>
                </template>

                <template #item.qty="{ item }">
                    <div class="cart-qty-wrap" @click.stop>
                        <v-number-input
                            v-model="item.qty"
                            control-variant="hidden"
                            variant="outlined"
                            density="compact"
                            :precision="2"
                            :label="__('Qty')"
                            hide-details="auto"
                            class="cart-qty-input"
                            @change="update_number(item, 'qty', item.qty)"
                        />
                    </div>
                </template>

                <template #item.amount="{ item }">
                    <div class="cart-item-amount text-right" v-html="frappe_.format(item.amount, {'fieldtype': 'Currency'})"></div>
                </template>

                <template #item.actions="{ item }">
                    <v-btn
                        icon="mdi-delete"
                        variant="text"
                        density="compact"
                        color="error"
                        @click.stop="deleteItemFromCart(item)"
                    />
                </template>

                <template #expanded-row="{ columns, item }">
                    <tr class="cart-expanded-row">
                        <td :colspan="columns.length">
                            <v-row dense class="pt-2">
                                <v-col cols="12" md="6" @click.stop>
                                    <v-number-input
                                        v-model="item.rate"
                                        control-variant="hidden"
                                        variant="outlined"
                                        density="compact"
                                        :disabled="!allow_rate_change"
                                        :precision="2"
                                        :label="__('Rate') + ': ' + item.price_list_rate + ' ' + priceListCurrency"
                                        hide-details="auto"
                                        @change="update_number(item, 'rate', item.rate)"
                                    />
                                </v-col>
                                <v-col cols="12" md="6" @click.stop>
                                    <v-number-input
                                        v-if="item.discount_type === 'Amount'"
                                        v-model="item.discount_amount"
                                        control-variant="hidden"
                                        variant="outlined"
                                        density="compact"
                                        :precision="2"
                                        :label="__('Discount')"
                                        :disabled="!allow_discount_change"
                                        hide-details="auto"
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
                                        hide-details="auto"
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
                        </td>
                    </tr>
                </template>
            </v-data-table>
        </div>

        <v-divider class="my-2" />

        <div class="d-flex justify-space-between align-center">
            <div class="text-subtitle-1">{{ __('Total') }}</div>
            <div class="text-h6" v-html="frappe_.format(posFrm?.doc?.total, {'fieldtype': 'Currency'})"></div>
        </div>

        <div v-if="allow_discount_change" class="d-flex justify-space-between align-center mt-2 gap-3" @click.stop>
            <div class="text-subtitle-2 text-medium-emphasis flex-shrink-0">{{ __('Discount') }}</div>
            <div class="invoice-discount-input">
                <v-number-input
                    v-if="invoiceDiscountType === 'Amount'"
                    v-model="posFrm.doc.discount_amount"
                    control-variant="hidden"
                    variant="outlined"
                    density="compact"
                    :precision="2"
                    :min="0"
                    hide-details
                    @change="applyInvoiceDiscount"
                >
                    <template #append-inner>
                        <v-btn size="x-small" variant="text" @click.stop="toggleInvoiceDiscountType">
                            {{ priceListCurrency }}
                        </v-btn>
                    </template>
                </v-number-input>
                <v-number-input
                    v-else
                    v-model="posFrm.doc.additional_discount_percentage"
                    control-variant="hidden"
                    variant="outlined"
                    density="compact"
                    :precision="2"
                    :min="0"
                    :max="100"
                    hide-details
                    @change="applyInvoiceDiscount"
                >
                    <template #append-inner>
                        <v-btn size="x-small" variant="text" @click.stop="toggleInvoiceDiscountType" text="%" />
                    </template>
                </v-number-input>
            </div>
        </div>

        <div class="d-flex justify-space-between align-center mt-1">
            <div class="text-subtitle-1 font-weight-bold">{{ __('Net Total') }}</div>
            <div class="text-h6 font-weight-bold" v-html="frappe_.format(posFrm?.doc?.grand_total, {'fieldtype': 'Currency'})"></div>
        </div>

        <v-btn color="green-lighten-1" class="mt-3" block @click="emit('checkout')">
            {{ __('Checkout') }}
        </v-btn>
    </VCard>
</template>

<script setup>
    import { computed, ref, triggerRef } from 'vue'
    import { usePosStore } from '../../../store/posStore';
    import {storeToRefs} from 'pinia';
    import { VCard } from 'vuetify/components';
    const __ = window.__;
    const frappe_ = frappe;
    const posStore = usePosStore();
    const {posFrm, posProfileData} = storeToRefs(posStore);
    const {update_cart} = posStore;
    const expanded = ref([]);

    const emit = defineEmits(['checkout']);
    const posCartItems = computed(() => posFrm.value?.doc?.items || [])
    const cartItemsPerPage = computed(() => posCartItems.value.length || 1)
    const priceListCurrency = computed(() => posFrm.value?.doc?.price_list_currency || "")
    const allow_discount_change = computed(() => posProfileData.value?.allow_discount_change)
    const allow_rate_change = computed(() => posProfileData.value?.allow_rate_change)
    const cartHeaders = computed(() => [
        { title: '', key: 'data-table-expand', sortable: false, width: '42px' },
        { title: __('Item'), key: 'item_name', sortable: false },
        { title: __('Qty'), key: 'qty', sortable: false, width: '132px' },
        { title: __('Amount'), key: 'amount', sortable: false, align: 'end', width: '132px' },
        { title: '', key: 'actions', sortable: false, align: 'end', width: '52px' },
    ])
    
    const update_number = async (item, field, value) => {
        update_cart({
            field: field,
            value: value,
            item: item,
            is_number: true
        });
    }

    const deleteItemFromCart = async (item) => {
        expanded.value = expanded.value.filter((value) => value !== item.idx);
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

    const invoiceDiscountType = ref('Amount')

    async function applyInvoiceDiscount() {
        await posFrm.value.script_manager.trigger("calculate_taxes_and_totals");
        triggerRef(posFrm);
    }

    function toggleInvoiceDiscountType() {
        if (invoiceDiscountType.value === 'Percentage') {
            invoiceDiscountType.value = 'Amount'
            posFrm.value.doc.additional_discount_percentage = 0
        } else {
            invoiceDiscountType.value = 'Percentage'
            posFrm.value.doc.discount_amount = 0
        }
        applyInvoiceDiscount()
    }
</script>

<style scoped>
    .cart-card {
        border: 1px solid var(--v-pos-panel-border);
        background: var(--v-pos-panel-background);
        box-shadow: var(--v-pos-panel-shadow);
        transition: var(--v-theme-transition);
    }

    .cart-scroll-container {
        max-height: clamp(160px, 40dvh, 700px);
        overflow-y: auto;
        padding-inline-end: 4px;
    }

    .cart-table {
        background: transparent;
    }

    .cart-table :deep(.v-table__wrapper) {
        overflow: visible;
    }

    .cart-table :deep(table) {
        border-collapse: separate;
        border-spacing: 0 8px;
    }

    .cart-table :deep(tbody tr) {
        background: var(--v-pos-field-background);
    }

    .cart-table :deep(tbody tr:not(.cart-expanded-row) td) {
        border-top: 1px solid var(--v-pos-panel-border-soft);
        border-bottom: 1px solid var(--v-pos-panel-border-soft);
        padding-top: 10px;
        padding-bottom: 10px;
    }

    .cart-table :deep(tbody tr:not(.cart-expanded-row) td:first-child) {
        border-inline-start: 1px solid var(--v-pos-panel-border-soft);
        border-start-start-radius: 12px;
        border-end-start-radius: 12px;
    }

    .cart-table :deep(tbody tr:not(.cart-expanded-row) td:last-child) {
        border-inline-end: 1px solid var(--v-pos-panel-border-soft);
        border-start-end-radius: 12px;
        border-end-end-radius: 12px;
    }

    .cart-item-name {
        font-size: 0.95rem;
        font-weight: 600;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
    }

    .cart-item-amount {
        font-size: 0.9rem;
        color: rgb(var(--v-pos-text-muted));
    }

    .cart-qty-wrap {
        width: 112px;
    }

    .cart-qty-input :deep(.v-input__details) {
        display: none;
    }

    .cart-expanded-row td {
        padding-block-end: 12px !important;
        padding-inline: 12px !important;
        border: 1px solid var(--v-pos-panel-border-soft);
        border-top: 0;
        border-end-start-radius: 12px;
        border-end-end-radius: 12px;
        background: var(--v-pos-panel-background);
    }

    .cart-table :deep(.v-data-table__td) {
        vertical-align: middle;
    }

    .cart-table :deep(.v-data-table__tr--expanded td) {
        border-bottom: 0;
        border-end-start-radius: 0 !important;
        border-end-end-radius: 0 !important;
    }

    .cart-table :deep(.v-btn--icon.v-data-table-expand__content) {
        color: rgb(var(--v-pos-text-muted));
    }
    .cart-qty-input {
        width: 100%;
    }
    td.v-data-table__td.v-data-table-column--no-padding.v-data-table-column--align-start.v-data-table__td--expanded-row {
        display: none;
    }

    .invoice-discount-input {
        width: 160px;
    }
</style>