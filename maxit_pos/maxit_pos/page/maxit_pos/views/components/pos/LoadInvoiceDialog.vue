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
              <th>Invoice ID</th>
              <th>Customer Name</th>
              <th>Amount</th>
              <th>Action</th>
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
                  @click="selectInvoice(inv)"
                >
                  LOAD
                </v-btn>
              </td>
            </tr>
          </tbody>
        </v-table>
      </v-card-text>

      <v-card-actions>
        <v-spacer />
        <v-btn text @click="closeDialog">Close</v-btn>
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
