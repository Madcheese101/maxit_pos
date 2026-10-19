<template>
    <div class="cart">
        <div ref="linesEl" class="cart-lines">
            <div v-if="!posCartItems.length" class="cart-empty text-medium-emphasis">
                <v-icon icon="mdi-cart-outline" size="32" />
                <div>{{ __('Cart is empty') }}</div>
            </div>

            <div
                v-for="item in posCartItems"
                :key="item.idx"
                class="cart-line"
                :class="{ 'cart-line--open': expanded === item.idx }"
            >
                <div class="cart-line__head" @click="toggleExpanded(item)">
                    <div class="cart-line__name">{{ item.idx }}. {{ item.item_name }}</div>
                    <v-btn
                        icon="mdi-delete-outline"
                        variant="text"
                        size="x-small"
                        color="error"
                        :aria-label="__('Delete')"
                        @click.stop="deleteItemFromCart(item)"
                    />
                </div>

                <div class="cart-line__row">
                    <div class="cart-line__rate" @click="toggleExpanded(item)">
                        {{ formatNumber(item.rate) }}
                        <span v-if="flt(item.discount_percentage)" class="text-success">
                            -{{ flt(item.discount_percentage, 2) }}%
                        </span>
                    </div>
                    <div class="qty-stepper">
                        <v-btn
                            icon="mdi-minus"
                            variant="tonal"
                            size="x-small"
                            :disabled="Math.abs(flt(item.qty)) <= 1"
                            :aria-label="__('Qty') + ' -'"
                            @click="stepQty(item, -1)"
                        />
                        <input
                            class="qty-stepper__input"
                            type="number"
                            inputmode="decimal"
                            :value="item.qty"
                            :aria-label="__('Qty')"
                            @change="onQtyChange(item, $event)"
                        />
                        <v-btn
                            icon="mdi-plus"
                            variant="tonal"
                            size="x-small"
                            :aria-label="__('Qty') + ' +'"
                            @click="stepQty(item, 1)"
                        />
                    </div>
                    <div class="cart-line__amount">{{ formatNumber(item.amount) }}</div>
                </div>

                <v-expand-transition>
                    <div v-if="expanded === item.idx" class="cart-line__details">
                        <v-number-input
                            v-model="item.rate"
                            control-variant="hidden"
                            variant="outlined"
                            density="compact"
                            :disabled="!allow_rate_change"
                            :precision="2"
                            :label="__('Rate') + ': ' + item.price_list_rate + ' ' + priceListCurrency"
                            hide-details
                            @change="update_number(item, 'rate', item.rate)"
                        />
                        <v-number-input
                            v-if="item.discount_type === 'Amount'"
                            v-model="item.discount_amount"
                            control-variant="hidden"
                            variant="outlined"
                            density="compact"
                            :precision="2"
                            :label="__('Discount')"
                            :disabled="!allow_discount_change"
                            hide-details
                            @change="update_number(item, 'discount_amount', item.discount_amount)"
                        >
                            <template #append-inner>
                                <v-btn size="small" variant="text" @click.stop="toggleDiscountType(item)">
                                    {{ priceListCurrency }}
                                </v-btn>
                            </template>
                        </v-number-input>
                        <v-number-input
                            v-else
                            v-model="item.discount_percentage"
                            control-variant="hidden"
                            variant="outlined"
                            density="compact"
                            :precision="2"
                            :label="__('Discount %')"
                            :disabled="!allow_discount_change"
                            hide-details
                            @change="update_number(item, 'discount_percentage', item.discount_percentage)"
                        >
                            <template #append-inner>
                                <v-btn size="small" variant="text" text="%" @click.stop="toggleDiscountType(item)" />
                            </template>
                        </v-number-input>
                    </div>
                </v-expand-transition>
            </div>
        </div>

        <div class="cart-footer">
            <div class="cart-total-row">
                <span class="text-medium-emphasis">{{ __('Total') }}</span>
                <span v-html="frappe_.format(invoice?.total, {'fieldtype': 'Currency'})"></span>
            </div>

            <div v-if="allow_edit_additional_discount && invoice" class="cart-total-row">
                <span class="text-medium-emphasis">{{ __('Discount') }}</span>
                <div class="invoice-discount-input">
                    <v-number-input
                        v-if="invoiceDiscountType === 'Amount'"
                        v-model="invoice.discount_amount"
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
                        v-model="invoice.additional_discount_percentage"
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

            <div class="cart-total-row cart-total-row--net">
                <span>{{ __('Net Total') }}</span>
                <span v-html="frappe_.format(invoice?.grand_total, {'fieldtype': 'Currency'})"></span>
            </div>

            <v-btn
                color="success"
                variant="elevated"
                size="large"
                block
                prepend-icon="mdi-cash-register"
                class="flex-grow-0"
                :disabled="!posCartItems.length"
                @click="emit('checkout')"
            >
                {{ __('Checkout') }}
            </v-btn>
        </div>
    </div>
</template>

<script setup>
    import { computed, nextTick, ref, watch } from 'vue'
    import { usePosStore } from '../../../store/posStore';
    import {storeToRefs} from 'pinia';
    const __ = window.__;
    const frappe_ = frappe;
    const flt = window.flt;
    const formatNumber = (value) => window.format_number(value);
    const posStore = usePosStore();
    const {invoice, posProfileData} = storeToRefs(posStore);
    const {update_cart, remove_item, calculate_totals} = posStore;
    const expanded = ref(null);
    const linesEl = ref(null);

    const emit = defineEmits(['checkout']);
    const posCartItems = computed(() => invoice.value?.items || [])
    const priceListCurrency = computed(() => invoice.value?.currency || "")
    const allow_discount_change = computed(() => posProfileData.value?.allow_discount_change)
    const allow_rate_change = computed(() => posProfileData.value?.allow_rate_change)
    const allow_edit_additional_discount = computed(() => posProfileData.value?.allow_edit_additional_discount)

    // keep the newest line visible after adding an item
    watch(() => posCartItems.value.length, (length, oldLength) => {
        if (length <= oldLength) return;
        nextTick(() => linesEl.value?.scrollTo({ top: linesEl.value.scrollHeight }));
    });

    const update_number = (item, field, value) => {
        return update_cart({
            field: field,
            value: value,
            item: item,
            is_number: true
        });
    }

    // returns hold negative quantities, so "+" adds one more unit to the return
    const stepQty = (item, direction) => {
        const step = invoice.value.is_return ? -1 : 1;
        update_number(item, 'qty', flt(item.qty) + direction * step);
    }

    const onQtyChange = async (item, event) => {
        await update_number(item, 'qty', event.target.value);
        // the stock check may have rejected the typed qty
        event.target.value = item.qty;
    }

    const toggleExpanded = (item) => {
        expanded.value = expanded.value === item.idx ? null : item.idx;
    }

    const deleteItemFromCart = (item) => {
        expanded.value = null;
        remove_item(item);
    }

    function toggleDiscountType(item) {
        if (item.discount_type === 'Percentage') {
            item.discount_type = 'Amount'
            update_cart({ field: 'discount_percentage', value: 0, item, is_number: true })
        } else {
            item.discount_type = 'Percentage'
            update_cart({ field: 'discount_amount', value: 0, item, is_number: true })
        }
    }

    const invoiceDiscountType = ref('Amount')

    function applyInvoiceDiscount() {
        calculate_totals();
    }

    function toggleInvoiceDiscountType() {
        if (invoiceDiscountType.value === 'Percentage') {
            invoiceDiscountType.value = 'Amount'
            invoice.value.additional_discount_percentage = 0
        } else {
            invoiceDiscountType.value = 'Percentage'
            invoice.value.discount_amount = 0
        }
        applyInvoiceDiscount()
    }
</script>

<style scoped>
    .cart {
        display: flex;
        flex-direction: column;
        flex: 1;
        min-height: 0;
    }

    .cart-lines {
        flex: 1;
        min-height: 0;
        overflow-y: auto;
        display: flex;
        flex-direction: column;
        gap: var(--maxit-gap-sm);
        padding-block: 2px;
    }

    .cart-empty {
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        gap: 4px;
        flex: 1;
        min-height: 96px;
    }

    .cart-line {
        flex-shrink: 0;
        border: 1px solid var(--v-pos-panel-border-soft);
        border-radius: 10px;
        background: var(--v-pos-field-background);
        padding: 8px 10px;
    }

    .cart-line--open {
        border-color: rgb(var(--v-theme-primary));
    }

    .cart-line__head {
        display: flex;
        align-items: flex-start;
        gap: 4px;
        cursor: pointer;
    }

    .cart-line__name {
        flex: 1;
        min-width: 0;
        font-size: 0.875rem;
        font-weight: 600;
        line-height: 1.35;
        padding-block-start: 2px;
    }

    .cart-line__row {
        display: flex;
        align-items: center;
        gap: 8px;
        margin-block-start: 4px;
    }

    .cart-line__rate {
        flex: 1;
        min-width: 0;
        font-size: 0.8125rem;
        color: rgb(var(--v-pos-text-muted));
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
        cursor: pointer;
    }

    .cart-line__amount {
        min-width: 72px;
        text-align: end;
        font-size: 0.875rem;
        font-weight: 700;
        white-space: nowrap;
    }

    .qty-stepper {
        display: flex;
        align-items: center;
        gap: var(--maxit-gap-xs);
        flex-shrink: 0;
    }

    .qty-stepper__input {
        width: 52px;
        height: 28px;
        padding: 0 4px;
        border: 1px solid var(--v-pos-panel-border);
        border-radius: 6px;
        background: transparent;
        color: inherit;
        font-size: 0.875rem;
        font-weight: 600;
        text-align: center;
        -moz-appearance: textfield;
    }

    .qty-stepper__input::-webkit-outer-spin-button,
    .qty-stepper__input::-webkit-inner-spin-button {
        -webkit-appearance: none;
        margin: 0;
    }

    .cart-line__details {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(130px, 1fr));
        gap: 8px;
        padding-block-start: 10px;
    }

    .cart-footer {
        display: flex;
        flex-direction: column;
        gap: var(--maxit-gap-sm);
        padding-block-start: var(--maxit-gap);
        margin-block-start: var(--maxit-gap-xs);
        border-top: 1px solid var(--v-pos-panel-border-soft);
    }

    .cart-total-row {
        display: flex;
        align-items: center;
        justify-content: space-between;
        gap: 12px;
        font-size: 0.875rem;
    }

    .cart-total-row--net {
        font-size: 1.05rem;
        font-weight: 700;
    }

    .invoice-discount-input {
        width: 150px;
    }
</style>
