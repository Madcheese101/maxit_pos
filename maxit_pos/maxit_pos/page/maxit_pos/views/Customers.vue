<template>
  <v-main class="customers-view pa-3 pa-md-6">
    <v-row class="customers-shell" align="stretch">
      <v-col v-show="!isMobile || !showDetailsOnMobile" cols="12" md="4" lg="3" class="customers-column">
        <v-card class="h-100 customers-card customers-list-panel" rounded="xl" variant="elevated">
          <v-card-item class="pb-2">
            <div class="d-flex align-center justify-space-between gap-2 mb-3">
              <div>
                <div class="text-overline text-medium-emphasis">{{ __('Customers') }}</div>
                <div class="text-h6 font-weight-bold">{{ __('Select Customer') }}</div>
              </div>
              <v-chip size="small" color="primary" variant="tonal">
                {{ customers.length }}
              </v-chip>
            </div>

            <v-text-field
              v-model="searchTerm"
              density="comfortable"
              :placeholder="__('Search customer by code or name')"
              prepend-inner-icon="mdi-magnify"
              variant="solo-filled"
              hide-details
              single-line
              rounded="lg"
              @keydown.enter="fetchCustomers()"
            />
          </v-card-item>

          <v-divider />

          <v-card-text class="pt-3 px-2 customers-list-body">
            <div v-if="isLoadingList" class="px-2 py-5">
              <v-skeleton-loader type="list-item-two-line, list-item-two-line, list-item-two-line" />
            </div>

            <v-list
              v-else-if="customers.length"
              lines="two"
              color="primary"
              nav
              rounded="lg"
              class="customers-list"
              v-model:selected="selected"
            >
              <v-list-item
                v-for="customer in customers"
                :key="customer.name"
                :value="customer.name"
                :title="customer.customer_name || customer.name"
                :subtitle="customerSubtitle(customer)"
                rounded="lg"
                class="mb-1"
              >
                <template #append>
                  <v-chip size="small" color="secondary" variant="tonal">
                    {{ customer.linked_invoices || 0 }}
                  </v-chip>
                </template>
              </v-list-item>
            </v-list>

            <v-alert
              v-else
              type="info"
              variant="tonal"
              density="compact"
              class="mt-2"
            >
              {{ __('No customers found for this filter.') }}
            </v-alert>
          </v-card-text>
        </v-card>
      </v-col>

      <v-col v-show="!isMobile || showDetailsOnMobile" cols="12" md="8" lg="9" class="customers-column">
        <v-card class="h-100 customers-card" rounded="xl" variant="elevated">
          <v-card-item class="pb-0">
            <div class="d-flex align-center justify-space-between flex-wrap gap-3">
              <div class="d-flex align-center gap-2">
                <v-btn
                  v-if="isMobile"
                  icon="mdi-arrow-left"
                  variant="text"
                  size="small"
                  @click="showDetailsOnMobile = false"
                />

                <div v-if="selectedCustomer">
                  <div class="text-overline text-medium-emphasis">{{ __('Customer Details') }}</div>
                  <div class="text-h6 font-weight-bold">
                    {{ selectedCustomer.customer_name || selectedCustomer.name }}
                  </div>
                </div>

                <div v-else>
                  <div class="text-overline text-medium-emphasis">{{ __('Customer Details') }}</div>
                  <div class="text-h6 font-weight-bold">{{ __('No Customer Selected') }}</div>
                </div>
              </div>

              <div v-if="selectedCustomer" class="d-flex align-center gap-2">
                <v-btn
                  size="small"
                  variant="tonal"
                  color="success"
                  :loading="isSavingName"
                  :disabled="!canSaveName"
                  @click="saveCustomerName"
                >
                  {{ __('Save') }}
                </v-btn>
              </div>
            </div>
          </v-card-item>

          <v-card-text class="pt-4">
            <v-alert
              v-if="!selectedCustomer"
              type="info"
              variant="tonal"
            >
              {{ __('Select a customer from the left panel to view details.') }}
            </v-alert>

            <template v-else>
              <v-row dense class="mb-2">
                <v-col cols="12" sm="6" md="3">
                  <v-card class="stat-card" rounded="lg" variant="tonal" color="primary">
                    <v-card-text>
                      <div class="text-caption text-medium-emphasis">{{ __('Customer ID') }}</div>
                      <div class="text-body-1 font-weight-bold text-truncate">{{ selectedCustomer.name }}</div>
                    </v-card-text>
                  </v-card>
                </v-col>

                <v-col cols="12" sm="6" md="3">
                  <v-card class="stat-card" rounded="lg" variant="tonal" color="success" @click="openCustomerOrders" style="cursor: pointer;">
                    <v-card-text>
                      <div class="text-caption text-medium-emphasis">{{ __('Linked Invoices') }}</div>
                      <div class="text-body-1 font-weight-bold">{{ selectedCustomer.linked_invoices || 0 }}</div>
                    </v-card-text>
                  </v-card>
                </v-col>

                <v-col cols="12" sm="6" md="3">
                  <v-card class="stat-card" rounded="lg" variant="tonal" color="warning" @click="openContactDialog" style="cursor: pointer;">
                    <v-card-text>
                      <div class="text-caption text-medium-emphasis">{{ __('Primary Contact') }}</div>
                      <div class="text-body-1 font-weight-bold text-truncate">
                        {{ selectedCustomer.customer_primary_contact || __('Not linked') }}
                      </div>
                    </v-card-text>
                  </v-card>
                </v-col>
                <v-col cols="12" sm="6" md="3">
                  <v-card class="stat-card" rounded="lg" variant="tonal" color="info" @click="openAddressDialog" style="cursor: pointer;">
                    <v-card-text>
                      <div class="text-caption text-medium-emphasis">{{ __('Primary Address') }}</div>
                      <div class="text-body-1 font-weight-bold text-truncate">
                        {{ selectedCustomer.customer_primary_address || __('Not linked') }}
                      </div>
                    </v-card-text>
                  </v-card>
                </v-col>
              </v-row>

              <v-row dense class="mt-1">
                <v-col cols="12" md="12">
                  <v-text-field
                    v-model="nameDraft"
                    :label="__('Name')"
                    variant="solo-filled"
                    density="comfortable"
                    hide-details="auto"
                  />
                </v-col>

                <v-col cols="12" md="6">
                  <v-text-field
                    :model-value="selectedCustomer.email_id || ''"
                    :label="__('Email')"
                    variant="solo-filled"
                    density="comfortable"
                    readonly
                    hide-details
                  />
                </v-col>

                <v-col cols="12" md="6">
                  <v-text-field
                    :model-value="contactPhone"
                    :label="__('Mobile / Phone')"
                    variant="solo-filled"
                    density="comfortable"
                    readonly
                    hide-details
                  />
                </v-col>

                <v-col cols="12" md="6">
                  <v-combobox
                    v-model="primaryContactDraft"
                    :items="contactOptions"
                    :label="__('Primary Contact')"
                    :disabled="!contactOptions.length"
                    variant="solo-filled"
                    density="comfortable"
                    clearable
                    hide-details="auto"
                  />
                </v-col>

                <v-col cols="12" md="6">
                  <v-combobox
                    v-model="primaryAddressDraft"
                    :items="addressOptions"
                    :label="__('Primary Address')"
                    :disabled="!addressOptions.length"
                    variant="solo-filled"
                    density="comfortable"
                    clearable
                    hide-details="auto"
                  />
                </v-col>

                <v-col cols="12">
                  <v-text-field
                    :model-value="selectedCustomer.address_display || ''"
                    :label="__('Address')"
                    variant="solo-filled"
                    density="comfortable"
                    readonly
                    hide-details
                  />
                </v-col>
              </v-row>
            </template>
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>
  </v-main>
</template>

<script setup>
import { ref, watch, computed } from 'vue';
import { useRouter } from 'vue-router';
import { useDisplay } from 'vuetify';

const __ = window.__;

const router = useRouter();
const { smAndDown } = useDisplay();

const isMobile = computed(() => smAndDown.value);
const showDetailsOnMobile = ref(false);

const customers = ref([]);
const selected = ref([]);
const selectedCustomer = ref(null);
const searchTerm = ref('');
const nameDraft = ref('');
const primaryContactDraft = ref('');
const primaryAddressDraft = ref('');
const isLoadingList = ref(false);
const isSavingName = ref(false);
let searchTimeout = null;

const contactPhone = computed(() => {
  if (!selectedCustomer.value) return '';
  return selectedCustomer.value.mobile_no || selectedCustomer.value.phone || '';
});

const contactOptions = computed(() => {
  return selectedCustomer.value?.contact_options || [];
});

const addressOptions = computed(() => {
  return selectedCustomer.value?.address_options || [];
});

const canSaveName = computed(() => {
  if (!selectedCustomer.value || isSavingName.value) return false;
  const nextName = (nameDraft.value || '').trim();
  const currentName = (selectedCustomer.value.customer_name || '').trim();

  const nextPrimaryContact = (primaryContactDraft.value || '').trim();
  const currentPrimaryContact = (selectedCustomer.value.customer_primary_contact || '').trim();

  const nextPrimaryAddress = (primaryAddressDraft.value || '').trim();
  const currentPrimaryAddress = (selectedCustomer.value.customer_primary_address || '').trim();

  return (
    (!!nextName && nextName !== currentName)
    || nextPrimaryContact !== currentPrimaryContact
    || nextPrimaryAddress !== currentPrimaryAddress
  );
});

const customerSubtitle = (customer) => {
  const email = customer.email_id || __('No email');
  const phone = customer.mobile_no || customer.phone || __('No phone');
  return `${email} - ${phone}`;
};

const applySelection = () => {
  const selectedName = selected.value[0];
  if (!selectedName) {
    selectedCustomer.value = null;
    nameDraft.value = '';
    showDetailsOnMobile.value = false;
    return;
  }

  const customer = customers.value.find((row) => row.name === selectedName) || null;
  selectedCustomer.value = customer;
  nameDraft.value = customer?.customer_name || customer?.name || '';
  primaryContactDraft.value = customer?.customer_primary_contact || '';
  primaryAddressDraft.value = customer?.customer_primary_address || '';
  showDetailsOnMobile.value = true;
};

const fetchCustomers = () => {
  const previousSelection = selected.value[0] || '';
  isLoadingList.value = true;
  frappe.call({
    method: 'maxit_pos.maxit_pos.page.maxit_pos.api.api.get_customers_list',
    args: {
      search_term: searchTerm.value || '',
    },
  }).then((response) => {
    customers.value = response.message || [];

    if (previousSelection && customers.value.some((row) => row.name === previousSelection)) {
      selected.value = [previousSelection];
    } else {
      selected.value = [];
    }
    applySelection();
    isLoadingList.value = false;
  }).catch(() => {
    customers.value = [];
    selected.value = [];
    applySelection();
    isLoadingList.value = false;
    frappe.show_alert({
      indicator: 'red',
      message: __('Unable to load customers.'),
    }, 5);
  });
};

const saveCustomerName = () => {
  if (!selectedCustomer.value || !canSaveName.value) return;

  isSavingName.value = true;
  frappe.call({
    method: 'maxit_pos.maxit_pos.page.maxit_pos.api.api.update_customer_name',
    args: {
      customer: selectedCustomer.value.name,
      customer_name: (nameDraft.value || '').trim(),
      customer_primary_contact: (primaryContactDraft.value || '').trim(),
      customer_primary_address: (primaryAddressDraft.value || '').trim(),
    },
  }).then((response) => {
    const updated = response.message || {};
    const idx = customers.value.findIndex((row) => row.name === updated.name);
    if (idx !== -1) {
      customers.value[idx] = {
        ...customers.value[idx],
        customer_name: updated.customer_name,
        customer_primary_contact: updated.customer_primary_contact,
        customer_primary_address: updated.customer_primary_address,
        email_id: updated.email_id,
        mobile_no: updated.mobile_no,
        phone: updated.phone,
        address_display: updated.address_display,
        contact_options: updated.contact_options || customers.value[idx].contact_options || [],
        address_options: updated.address_options || customers.value[idx].address_options || [],
      };
      selectedCustomer.value = customers.value[idx];
    }
    nameDraft.value = updated.customer_name || nameDraft.value;
    primaryContactDraft.value = updated.customer_primary_contact || '';
    primaryAddressDraft.value = updated.customer_primary_address || '';
    isSavingName.value = false;

    frappe.show_alert({
      indicator: 'green',
      message: __('Customer updated successfully.'),
    }, 5);
  }).catch(() => {
    isSavingName.value = false;
    frappe.show_alert({
      indicator: 'red',
      message: __('Unable to save customer name.'),
    }, 5);
  });
};

const openContactDialog = () => {
  const contactName = selectedCustomer.value?.customer_primary_contact;
  if (!contactName) {
    frappe.show_alert({
      indicator: 'orange',
      message: __('No primary contact linked for this customer.'),
    }, 5);
    return;
  }

  window.open(`/app/contact/${encodeURIComponent(contactName)}`, '_blank');
};

const openAddressDialog = () => {
  const addressName = selectedCustomer.value?.customer_primary_address;
  if (!addressName) {
    frappe.show_alert({
      indicator: 'orange',
      message: __('No primary address linked for this customer.'),
    }, 5);
    return;
  }

  window.open(`/app/address/${encodeURIComponent(addressName)}`, '_blank');
};

const openCustomerOrders = () => {
  if (!selectedCustomer.value?.name) return;
  router.push({
    name: 'Orders',
    query: { customer: selectedCustomer.value.name },
  });
};

watch(selected, applySelection);

watch(searchTerm, () => {
  clearTimeout(searchTimeout);
  searchTimeout = setTimeout(() => {
    fetchCustomers();
  }, 300);
});

fetchCustomers();
</script>

<style scoped>
.customers-view {
  min-height: calc(100dvh - var(--v-layout-top, 0px) - var(--v-layout-bottom, 0px));
  height: calc(100dvh - var(--v-layout-top, 0px) - var(--v-layout-bottom, 0px));
  overflow: hidden;
  background:
    radial-gradient(circle at top right, rgba(25, 118, 210, 0.09), transparent 42%),
    radial-gradient(circle at left bottom, rgba(76, 175, 80, 0.08), transparent 38%);
}

.customers-shell {
  height: 100%;
  min-height: 0;
}

.customers-column {
  display: flex;
  min-height: 0;
}

.customers-card {
  width: 100%;
  height: 100%;
  min-height: 0;
}

.customers-list-panel {
  display: flex;
  flex-direction: column;
}

.customers-list-body {
  flex: 1;
  min-height: 0;
  display: flex;
  flex-direction: column;
  overflow-y: auto;
}

.customers-list {
  flex: 1;
  min-height: 0;
  max-height: calc(100dvh - var(--v-layout-top, 0px) - var(--v-layout-bottom, 0px) - 260px);
  overflow-y: auto;
}

.customers-panel {
  border: 1px solid rgba(120, 144, 156, 0.24);
  background: linear-gradient(180deg, rgba(255, 255, 255, 0.94), rgba(248, 251, 255, 0.96));
  box-shadow: 0 10px 24px rgba(12, 28, 43, 0.08);
}

.customers-list :deep(.v-list-item--active) {
  background: rgba(25, 118, 210, 0.13);
}

.stat-card {
  border: 1px solid rgba(120, 144, 156, 0.18);
}

.actions-wrap {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}

@media (max-width: 960px) {
  .customers-view {
    min-height: calc(100dvh - var(--v-layout-top, 0px) - var(--v-layout-bottom, 0px));
    height: calc(100dvh - var(--v-layout-top, 0px) - var(--v-layout-bottom, 0px));
    padding: 10px;
  }

  .customers-list {
    max-height: calc(100dvh - var(--v-layout-top, 0px) - var(--v-layout-bottom, 0px) - 220px);
  }

  .actions-wrap {
    display: grid;
    grid-template-columns: 1fr;
  }
}
</style>