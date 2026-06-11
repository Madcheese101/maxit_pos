<template>
  <v-dialog v-model="internalModel" max-width="760">
    <v-card class="pay-dialog" rounded="xl">
      <v-card-item class="pb-2">
        <div class="d-flex align-center justify-space-between gap-2">
          <div>
            <div class="text-overline text-medium-emphasis">{{ __('Payment') }}</div>
            <div class="text-h6 font-weight-bold">{{ __('Allocate Invoice Payment') }}</div>
          </div>
          <v-chip color="primary" variant="tonal" size="small">
            {{ currency }}
          </v-chip>
        </div>
      </v-card-item>

      <v-divider />

      <v-card-text class="pt-4">
        <v-table class="rounded-lg overflow-hidden payment-table" density="comfortable">
          <thead>
            <tr>
              <th>{{ __('Payment Mode') }}</th>
              <th class="text-right">{{ __('Amount') }}</th>
            </tr>
          </thead>

          <tbody>
            <tr v-for="payment in payments" :key="payment.mode_of_payment">
              <td class="font-weight-medium">{{ payment.mode_of_payment }}</td>
              <td>
                <v-number-input
                  v-model="payment.amount"
                  :prefix="currency || ''"
                  control-variant="hidden"
                  variant="outlined"
                  density="comfortable"
                  :precision="2"
                  hide-details
                  @change="setTotal()"
                />
              </td>
            </tr>
          </tbody>
        </v-table>

        <v-row class="mt-3" dense>
          <v-col cols="12" sm="4">
            <v-sheet class="summary-card" color="primary" rounded="lg" variant="tonal">
              <div class="text-caption text-medium-emphasis">{{ __('Total Paid') }}</div>
              <div class="text-body-1 font-weight-bold">{{ totalPaid }} {{ currency }}</div>
            </v-sheet>
          </v-col>
          <v-col cols="12" sm="4">
            <v-sheet class="summary-card" color="warning" rounded="lg" variant="tonal">
              <div class="text-caption text-medium-emphasis">{{ __('Outstanding') }}</div>
              <div class="text-body-1 font-weight-bold">{{ outstandingAmount }} {{ currency }}</div>
            </v-sheet>
          </v-col>
          <v-col cols="12" sm="4">
            <v-sheet class="summary-card" :color="unallocatedAmount === 0 ? 'success' : 'secondary'" rounded="lg" variant="tonal">
              <div class="text-caption text-medium-emphasis">{{ __('Unallocated') }}</div>
              <div class="text-body-1 font-weight-bold">{{ unallocatedAmount }} {{ currency }}</div>
            </v-sheet>
          </v-col>
        </v-row>
      </v-card-text>

      <v-card-actions class="px-4 pb-4 pt-0 d-flex gap-2 flex-wrap">
        <v-spacer />
        <v-btn color="success" variant="elevated" prepend-icon="mdi-cash-check" @click="payInvoice">
          {{ __('Pay') }}
        </v-btn>
        <v-btn variant="tonal" @click="closeDialog">
          {{ __('Close') }}
        </v-btn>
      </v-card-actions>
    </v-card>
  </v-dialog>
</template>

<script setup>
  import { ref, watch } from "vue";
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
  border: 1px solid var(--v-pos-panel-border);
  background: var(--v-pos-panel-background);
  box-shadow: var(--v-pos-panel-shadow);
  transition: var(--v-theme-transition);
}

.payment-table {
  border: 1px solid var(--v-pos-panel-border-soft);
}

.summary-card {
  padding: 12px;
  border: 1px solid var(--v-pos-panel-border-soft);
}
</style>
