<template>
  <v-dialog v-model="internalModel" max-width="700">
    <v-card class="load-invoice-dialog" rounded="xl">
      <v-card-item class="pb-2">
        <div>
          <div class="text-overline text-medium-emphasis">{{ __('POS') }}</div>
          <div class="text-h6 font-weight-bold">{{ __('Select Invoice') }}</div>
        </div>
      </v-card-item>
      <v-divider />

      <v-card-text class="pt-4 dialog-body">
        <v-alert v-if="!invoices?.length" type="info" variant="tonal">
          {{ __('No draft invoices found.') }}
        </v-alert>

        <v-table v-else class="load-invoice-table" density="compact">
          <thead>
            <tr>
              <th>{{ __('Invoice ID') }}</th>
              <th>{{ __('Customer Name') }}</th>
              <th>{{ __('Amount') }}</th>
              <th>{{ __('Action') }}</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="inv in invoices" :key="inv.name">
              <td>{{ inv.name }}</td>
              <td>{{ inv.customer }}</td>
              <td>{{ inv.grand_total }}</td>
              <td>
                <v-btn
                  size="small"
                  color="primary"
                  variant="tonal"
                  @click="selectInvoice(inv)"
                >
                  {{ __('Load') }}
                </v-btn>
              </td>
            </tr>
          </tbody>
        </v-table>
      </v-card-text>

      <v-card-actions class="px-4 pb-4 pt-0">
        <v-spacer />
        <v-btn variant="tonal" @click="closeDialog">{{ __('Close') }}</v-btn>
      </v-card-actions>
    </v-card>
  </v-dialog>
</template>

<script setup>
  import { ref, watch } from "vue";

  const props = defineProps({
    modelValue: Boolean,
    invoices: Array
  });

  const emit = defineEmits(["update:modelValue", "load", "close"]);
  const __ = window.__;

  const internalModel = ref(props.modelValue);

  // Sync parent → child
  watch(
    () => props.modelValue,
    val => internalModel.value = val
  );

  // Sync child → parent
  watch(internalModel, val => emit("update:modelValue", val));

  function closeDialog() {
    internalModel.value = false;
    emit("close");
  }

  function selectInvoice(invoice) {
    emit("load", invoice);
    internalModel.value = false;
  }
</script>

<style scoped>
  .load-invoice-dialog {
    border: 1px solid var(--v-pos-panel-border);
    background: var(--v-pos-panel-background);
    transition: var(--v-theme-transition);
  }

  .dialog-body {
    max-height: 60vh;
    overflow-y: auto;
  }

  .load-invoice-table :deep(th) {
    font-weight: 700;
    white-space: nowrap;
  }
</style>
