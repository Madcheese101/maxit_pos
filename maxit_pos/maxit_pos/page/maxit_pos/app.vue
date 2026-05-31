<template>
    <!-- <v-progress-circular
      v-if="isLoading"
        :size="70"
        :width="7"
        class="justify-center"
        indeterminate
    ></v-progress-circular> -->
    <v-app :dir="getAppDirection()" class="maxit-pos-app">
      <v-locale-provider :rtl="isAppRTL()">
        <!-- sidebar -->
        <SideBar :showPosProfileDependent="showPosProfileDependent"/>
        <!-- Pages Views Container -->
        <v-main class="main-body-container">
            <router-view v-slot="{ Component }">
              <keep-alive include="Items">
                <component :is="Component" />
              </keep-alive>
            </router-view>
        </v-main>
        <v-dialog
          v-model="isLoading"
          max-width="100"
          persistent>
          <v-progress-circular
            :size="50"
            :width="7"
            indeterminate
            color="cyan-accent-2"
          ></v-progress-circular>
        </v-dialog>
      </v-locale-provider>
    </v-app>
  </template>
  
  
  <script setup>
    import SideBar from './views/components/SideBar.vue';
    import { usePosStore } from './store/posStore';
    import {storeToRefs} from 'pinia';
    import {ref, watch, onMounted} from 'vue';
    import { useTheme } from 'vuetify';
    const isLoading = ref(true);
    const props = defineProps(['posProfileData', 'appDefaults']);
    const posStore = usePosStore();
    const {activeVuetifyTheme} = storeToRefs(posStore);
    const {setAppDefaults, make_new_invoice, getAppDirection, isAppRTL} = posStore;
    const showPosProfileDependent = ref(props.posProfileData ? true : false);
    const theme = useTheme();

    watch(activeVuetifyTheme, (nextTheme) => {
      if (theme.global.name.value !== nextTheme) {
        theme.global.name.value = nextTheme;
      }
    }, { immediate: true });

    setAppDefaults(props.posProfileData, props.appDefaults)
    make_new_invoice().then(() => {
      isLoading.value = false;
    })

    frappe.realtime.on("shift_closed", (data) => { 
      
    });
    onMounted(async () => {
      if (frappe.realtime && typeof frappe.realtime.on === "function") {
        frappe.realtime.on("shift_closed", (data) => {
          console.log("Received shift_closed event:", data);
          if(!data.user_name || !data.closing_entry_name) return;
          if (data.user_name === frappe.session.user) window.location.reload();
        });
      }
    });
  </script>
  
  <style>
  .maxit-pos-app {
    --maxit-page-padding-mobile: 10px;
    --maxit-page-padding-short: 10px;
    --maxit-stat-padding: 16px;
    --maxit-stat-padding-compact: 12px;
    background: var(--v-pos-shell-background);
    color: rgb(var(--v-theme-on-background));
    transition: var(--v-theme-transition);
  }

  .main-body-container{
    background: var(--v-pos-shell-background);
    color: rgb(var(--v-theme-on-background));
    transition: var(--v-theme-transition);
  }

  @media (max-height: 768px) and (min-width: 960px) {
    .maxit-pos-app {
      --maxit-page-padding-short: 8px;
      --maxit-stat-padding: 14px;
      --maxit-stat-padding-compact: 10px;
    }
  }
  </style>