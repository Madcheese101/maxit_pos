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
    import {ref, watchEffect} from 'vue';
    import { useTheme } from 'vuetify';
    const isLoading = ref(true);
    const props = defineProps(['posProfileData', 'appDefaults']);
    const posStore = usePosStore();
    const {activeVuetifyTheme} = storeToRefs(posStore);
    const {setAppDefaults, make_new_invoice, getAppDirection, isAppRTL} = posStore;
    const showPosProfileDependent = ref(props.posProfileData ? true : false);
    const theme = useTheme();

    watchEffect(() => {
      theme.global.name.value = activeVuetifyTheme.value;
    });

    setAppDefaults(props.posProfileData, props.appDefaults)
    make_new_invoice().then(() => {
      isLoading.value = false;
    })
  </script>
  
  <style>
  .maxit-pos-app {
    background: var(--v-pos-shell-background);
    color: rgb(var(--v-theme-on-background));
    transition: var(--v-theme-transition);
  }

  .main-body-container{
    background: var(--v-pos-shell-background);
    color: rgb(var(--v-theme-on-background));
    transition: var(--v-theme-transition);
  }
  </style>