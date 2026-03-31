<template>
    <!-- <v-progress-circular
      v-if="isLoading"
        :size="70"
        :width="7"
        class="justify-center"
        indeterminate
    ></v-progress-circular> -->
    <v-app>
      <!-- sidebar -->
      <SideBar :showPosProfileDependent="showPosProfileDependent"/>
      <!-- Pages Views Container -->
      <v-main class="main-body-container">
        <div class="views-container ">
          <router-view/>
        </div>
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
    </v-app>
  </template>
  
  
  <script setup>
    import SideBar from './views/components/SideBar.vue';
    import { usePosStore } from './store/posStore';
    import {storeToRefs} from 'pinia';
    import {ref} from 'vue';
    const isLoading = ref(true);
    const props = defineProps(['posProfileData', 'appDefaults']);
    const posStore = usePosStore();
    const {posProfileData} = storeToRefs(posStore);
    const {setAppDefaults, make_new_invoice} = posStore;
    const showPosProfileDependent = ref(props.posProfileData ? true : false);

    setAppDefaults(props.posProfileData, props.appDefaults)
    make_new_invoice().then(() => {
      isLoading.value = false;
    })
  </script>
  
  <style>
  .main-body-container{
    background: #edf2f5;
  }
  </style>