<template>
  <v-dialog v-model="internalModel" max-width="700">
    <v-card>
      <v-card-title class="text-h6">
        Select Invoice
      </v-card-title>

      <v-card-text>
        <v-table>
          <thead>
            <tr>
              <th>{{ __('Payment Mode') }}</th>
              <th>{{ __('Amount') }}</th>
            </tr>
          </thead>

          <tbody>
            <tr v-for="payment in payments" :key="payment.mode_of_payment">
              <td>{{ payment.mode_of_payment }}</td>
              <td>
                <v-number-input 
                  class="mt-3"
                  v-model="payment.amount"
                  :prefix="pos_profile ? pos_profile.currency : ''"
                  control-variant="hidden"
                  variant="outlined"
                  density="compact"
                  :precision="2"
                  @change="setTotal()"
                />
              </td>
              <!-- <td>
                <v-btn
                  size="small"
                  color="primary"
                  @click="payInvoice(payment.name)"
                >
                  PAY
                </v-btn>
              </td> -->
            </tr>
          </tbody>
        </v-table>
        <div>
          <strong>{{__('Total Paid')}}:</strong> {{ totalPaid }} {{ currency }}<br>
          <strong>{{__('Invoice Outstanding Amount')}}:</strong> {{ outstandingAmount }} {{ currency }}<br>
          <strong>{{__('Unallocated Amount')}}:</strong> {{ unallocatedAmount }} {{ currency }}
        </div>
      </v-card-text>

      <v-card-actions>
        <v-spacer />
        <v-btn color="success" block @click="payInvoice">Pay</v-btn>
        <v-btn text @click="closeDialog">Close</v-btn>
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
