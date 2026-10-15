<template>
  <v-dialog v-model="internalModel" max-width="520" :fullscreen="xs">
    <v-card class="pay-dialog" :class="{ 'pay-dialog--fullscreen': xs }" :rounded="xs ? 0 : 'xl'">
      <v-card-item class="pb-2">
        <div class="text-h6 font-weight-bold">{{ __('Allocate Invoice Payment') }}</div>
      </v-card-item>

      <v-divider />

      <v-card-text class="pay-dialog__body">
        <div class="pay-dialog__due">
          <span class="text-medium-emphasis">{{ __('Outstanding') }}</span>
          <span class="font-weight-bold">{{ outstandingAmount }} {{ currency }}</span>
        </div>

        <div v-for="payment in payments" :key="payment.mode_of_payment" class="payment-row">
          <div class="payment-row__mode">{{ payment.mode_of_payment }}</div>
          <v-number-input
            v-model="payment.amount"
            control-variant="hidden"
            variant="outlined"
            density="compact"
            :precision="2"
            hide-details
            class="payment-row__input"
            @change="setTotal()"
          />
          <v-btn
            icon="mdi-cash-marker"
            variant="text"
            color="primary"
            size="small"
            :title="__('Pay full amount')"
            :aria-label="__('Pay full amount')"
            @click="fillOutstanding(payment)"
          />
        </div>

        <div class="pay-dialog__summary">
          <div class="pay-dialog__summary-row">
            <span>{{ __('Total Paid') }}</span>
            <span class="font-weight-bold">{{ totalPaid }} {{ currency }}</span>
          </div>
          <div class="pay-dialog__summary-row" :class="unallocatedAmount === 0 ? 'text-success' : ''">
            <span>{{ __('Unallocated') }}</span>
            <span class="font-weight-bold">{{ unallocatedAmount }} {{ currency }}</span>
          </div>
        </div>
      </v-card-text>

      <v-card-actions class="px-4 pb-4 pt-2 ga-2">
        <v-spacer />
        <v-btn variant="tonal" @click="closeDialog">
          {{ __('Close') }}
        </v-btn>
        <v-btn color="success" variant="elevated" prepend-icon="mdi-cash-check" @click="payInvoice">
          {{ __('Pay') }}
        </v-btn>
      </v-card-actions>
    </v-card>
  </v-dialog>
</template>

<script setup>
  import { ref, watch } from "vue";
  import { useDisplay } from "vuetify";
  const frappe_ = frappe;
  const __ = window.__;
  const props = defineProps({
    modelValue: Boolean,
    outstandingAmount: Number,
    paymentModes: Array,
    currency: String
  });

  const emit = defineEmits(["update:modelValue", "pay", "close"]);

  const internalModel = ref(props.modelValue);
  const payments = ref(props.paymentModes.map(pm => ({
    mode_of_payment: pm.mode_of_payment,
    amount: 0
  })));
  const unallocatedAmount = ref(0);
  const totalPaid = ref(0);
  const { xs } = useDisplay();
  

  // Sync parent → child
  watch(
    () => props.modelValue,
    val => internalModel.value = val
  );
  // Sync child → parent
  watch(internalModel, val => emit("update:modelValue", val));
  function setTotal() {
    totalPaid.value = payments.value.reduce((acc, payment) => acc + (payment.amount || 0), 0);
    unallocatedAmount.value = props.outstandingAmount - totalPaid.value;
  }

  function fillOutstanding(payment) {
    payments.value.forEach((row) => { row.amount = row === payment ? props.outstandingAmount : 0; });
    setTotal();
  }

  function closeDialog() {
    internalModel.value = false;
    emit("close");
  }

  function payInvoice(invoiceId) {
    if(totalPaid.value < 0 && props.outstandingAmount > 0) {
      frappe.show_alert(__('Total paid amount cannot be less than the invoice outstanding amount.'), 'error');
      return;
    }
    if(totalPaid.value === 0) {
      frappe.show_alert(__('Please enter an amount to pay.'), 'error');
      return;
    }
    emit("pay", payments.value)
    internalModel.value = false;
    payments.value = props.paymentModes.map(pm => ({
      mode_of_payment: pm.mode_of_payment,
      amount: 0
    }));
    totalPaid.value = 0;
    unallocatedAmount.value = 0;
  }
</script>

<style scoped>
.pay-dialog {
  display: flex;
  flex-direction: column;
  border: 1px solid var(--v-pos-panel-border);
  background: var(--v-pos-panel-background);
  box-shadow: var(--v-pos-panel-shadow);
  transition: var(--v-theme-transition);
}

.pay-dialog--fullscreen {
  background: rgb(var(--v-theme-surface));
}

.pay-dialog__body {
  display: flex;
  flex-direction: column;
  gap: var(--maxit-gap);
  flex: 1;
  overflow-y: auto;
}

.pay-dialog__due,
.pay-dialog__summary-row {
  display: flex;
  justify-content: space-between;
  gap: 12px;
}

.pay-dialog__due {
  padding: 10px 12px;
  border-radius: 10px;
  background: rgba(var(--v-theme-primary), 0.08);
}

.payment-row {
  display: flex;
  align-items: center;
  gap: var(--maxit-gap-sm);
}

.payment-row__mode {
  flex: 1;
  min-width: 0;
  font-weight: 600;
}

.payment-row__input {
  flex: 0 0 140px;
}

.pay-dialog__summary {
  display: flex;
  flex-direction: column;
  gap: var(--maxit-gap-xs);
  padding-block-start: var(--maxit-gap);
  border-top: 1px solid var(--v-pos-panel-border-soft);
}
</style>
