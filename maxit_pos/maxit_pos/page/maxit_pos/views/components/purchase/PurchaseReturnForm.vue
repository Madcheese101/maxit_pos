<template>
  <ItemPickerForm
    :title="__('Create Return')"
    :lines-title="__('Return Items')"
    :submit-label="__('Submit Return')"
    submit-icon="mdi-file-undo-outline"
    :submitting="isSubmitting"
    :ready="!!supplierBranch"
    :warehouse="posProfileData?.warehouse || ''"
    @cancel="emit('cancel')"
    @submit="onSubmit"
  >
    <template #fields>
      <v-autocomplete
        v-model="supplierBranch"
        :items="branchOptions"
        item-title="label"
        item-value="value"
        :label="__('Supplier Branch')"
        variant="outlined"
        density="compact"
        :loading="isLoadingBranches"
        hide-details="auto"
        clearable
        no-filter
        class="flex-grow-0"
        @update:search="(search) => loadBranchOptions(search)"
      />
    </template>
  </ItemPickerForm>
</template>

<script setup>
  import { storeToRefs } from 'pinia';
  import { computed, onMounted, ref } from 'vue';
  import { usePosStore } from '../../../store/posStore';
  import ItemPickerForm from '../ui/ItemPickerForm.vue';

  const emit = defineEmits(['cancel', 'created']);

  const __ = window.__;
  const frappe_ = window.frappe;
  const { posProfileData } = storeToRefs(usePosStore());
  const purchaseDoctype = computed(() => posProfileData.value?.purchase_doctype || 'Purchase Receipt');

  const supplierBranch = ref('');
  const branchOptions = ref([]);
  const isLoadingBranches = ref(false);
  const isSubmitting = ref(false);

  onMounted(() => loadBranchOptions());

  async function loadBranchOptions(search = '') {
    isLoadingBranches.value = true;
    try {
      const response = await frappe_.call({
        method: 'frappe.desk.search.search_link',
        args: {
          doctype: 'Supplier Branch',
          txt: search || '',
          page_length: 20,
          reference_doctype: purchaseDoctype.value,
          link_fieldname: 'supplier_branch',
        },
      });
      branchOptions.value = (response.message || []).map((item) => ({
        value: item.value,
        label: item.label || item.value,
        description: item.description || '',
      }));
    } catch (error) {
      frappe_.msgprint({
        title: __('Supplier Branch search failed'),
        indicator: 'red',
        message: error?.message || String(error),
      });
    } finally {
      isLoadingBranches.value = false;
    }
  }

  function onSubmit(items) {
    const totalQty = items.reduce((sum, item) => sum + item.qty, 0);
    frappe_.confirm(
      __('Submit a return of {0} items (total qty {1}) to {2}?', [items.length, totalQty, supplierBranch.value]),
      () => submitReturn(items)
    );
  }

  async function submitReturn(items) {
    isSubmitting.value = true;
    try {
      await frappe_.call({
        method: 'maxit_pos.maxit_pos.page.maxit_pos.api.purchase_vue.create_return_invoice',
        args: {
          supplier_branch: supplierBranch.value,
          items,
          cost_center: posProfileData.value?.cost_center || '',
          warehouse: posProfileData.value?.warehouse || '',
          purchase_doctype: purchaseDoctype.value,
        },
      });
      frappe_.show_alert({
        message: __('Return Invoice Created'),
        indicator: 'green'
      }, 5);
      emit('created');
    } finally {
      isSubmitting.value = false;
    }
  }
</script>
