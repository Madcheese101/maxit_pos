<template>
    <VCard rounded="lg" class="ma-auto">
      <!-- Card Header -->
      <VRow dense align="center" justify="center" class="ms-3 mt-3 mb-4 me-1">
        <!-- Card Title -->
        <VCol cols="5">
          <div class="font-weight-bold text-h6 ms-1 mb-2">{{ listType }}</div>
        </VCol>
        <!-- Refresh Button -->
        <VCol cols="3" class="align-end flex-column">
          <v-btn border variant="flat" icon="mdi-refresh"
          max-height="25" max-width="25" @click="refresh"></v-btn>
        </VCol>
        <!-- DatePicker Period Button -->
        <VCol>
          <v-btn border class="text-none ps-0" text="Select Period"
            prepend-icon="mdi-calendar-range" rounded="lg"
            block size="smal" variant="flat" min-height="25"
          >
            <div class="ps-1">Select Period</div>
            <!-- DatePicker Menu -->
            <v-menu :close-on-content-click="false" 
            activator="parent" v-model="menu" @click:outside="menuClosed">
              <v-card min-width="300">
                <v-date-picker
                  v-model="date_model"
                  @update:modelValue="onDateChange"
                  color="primary" show-adjacent-months
                  multiple="range"
                ></v-date-picker>
              </v-card>
            </v-menu>
          </v-btn>
        </VCol>
      </VRow>
      <div class="w-100 justify-start period-container">
        <div class="period-text font-weight-semi-bold">
          {{period_text}}
        </div>
      </div>
      <!-- List Section -->
      <VCardText>
        <v-list lines="two" max-height="300" class="overflow-y-auto">
          <v-list-item
            v-for="item in items"
            :key="item.order_id"
            class="border-b-sm"
          >
            <VRow>
              <VCol class="v-list-item__prepend justify-space-between">
                <div class="font-weight-bold">{{item.pickup_time}}</div>
                <v-avatar :color.once="get_random_color()">
                  <span class="text-h5">{{ get_intials(item.customer) }}</span>
                </v-avatar>
            </VCol>
              <VCol class="ps-0">
                <div class="v-list-item-title font-weight-semi-bold">{{ item.customer }}</div>
                <div class="v-list-item-subtitle">
                  <div>{{ item.email }}</div>
                  <div class="mt-1">{{ item.phone_no }}</div>
                </div>
              </VCol>
              <VCol class="v-list-item__append justify-end">
                <div class="font-weight-bold text-h7">
                  {{ '#'+item.order_id }}
                </div>
              </VCol>
            </VRow>
          </v-list-item>
        </v-list>
      </VCardText>
    </VCard>
</template>
 
<script setup>
  import {ref} from "vue";
  const dateFormat = {
      year: 'numeric',
        month: 'short',
        day: '2-digit',
  }
  // deconstruct props so that they can be accessed directly
  // instead of props.listType
  const {listType} = defineProps({
    listType: String
  })
  const items = ref([]);
  const period_text = ref("Today " + new Date().toLocaleDateString(undefined, dateFormat));
  const date_model = ref([]);
  const date_filter = ref([]);
  const menu = ref(false);
  
  const menuClosed = () => {
    if(date_model.value.length == 1){
      set_date_range();
    }
  }
  const onDateChange = () => {
      if (date_model.value.length > 1) {
        menu.value = false
        set_date_range()
      }
  }
  const set_date_range = () => {
    var range_length = date_model.value.length;
    var today = new Date().toLocaleDateString();
    var from = date_model.value[0].toLocaleDateString();
    var to = date_model.value[range_length - 1].toLocaleDateString();
    
    var from_formatted = date_model.value[0].toLocaleDateString(undefined, dateFormat);
    var to_formatted = date_model.value[range_length - 1].toLocaleDateString(undefined, dateFormat)
    date_filter.value = [date_model.value[0], date_model.value[range_length - 1]]
    
    if(today == from && range_length == 1) {
      period_text.value = 'Today ' + from_formatted;
      return;
    }
    period_text.value = from_formatted + ' -To- ' + to_formatted;

  }
  const get_intials = (full_name) => {
    return full_name.split(" ")[0][0] + full_name.split(" ")[1][0];
  };
  const get_data = () => {
    // pickup_time , customer , email
    // order_id , total_items
    var temp = [
        {
          pickup_time: "10:00 AM",
          order_id: "1050",
          customer: "Jack Rayan",
          email:"test@gmail.com",
          phone_no:"3"
        },
        {
          pickup_time: "09:00 AM",
          order_id: "1011",
          customer: "Simson Rayan",
          email:"test@gmail.com",
          phone_no:"1"
        },
        {
          pickup_time: "08:00 AM",
          order_id: "19",
          customer: "Dean Rayan",
          email:"test@gmail.com",
          phone_no:"5"
        },
        {
          pickup_time: "10:00 AM",
          order_id: "1050",
          customer: "Jack Rayan",
          email:"test@gmail.com",
          phone_no:"3"
        },
        {
          pickup_time: "09:00 AM",
          order_id: "1011",
          customer: "Simson Rayan",
          email:"test@gmail.com",
          phone_no:"1"
        },
        {
          pickup_time: "08:00 AM",
          order_id: "19",
          customer: "Dean Rayan",
          email:"test@gmail.com",
          phone_no:"5"
        }];
    if(listType == "Pickups"){
      return temp;
    }
    else if(listType == "Late Pickups"){
      return temp;
    }
    else if(listType == "Returns"){
      return temp;
    }
    else if(listType == "Late Returns"){
      return temp;
    }
    
    return [];
  }
  const refresh = () => {
    items.value = get_data();
  }
  const get_random_color = () => {
    return "hsl(" + Math.random() * 360 + ", 100%, 75%)";
  }
  // basically it is like created()
  items.value = get_data();
</script>

<style scoped>
  .font-weight-semi-bold{
    font-weight: 600;
  }
  .text-h7{
    font-size: 1.05rem;
    font-weight: 500;
    line-height: 1.6;
    letter-spacing: 0.0125em;
  }
  .period-container{
    border: 1px solid var(--v-pos-panel-border-soft);
    border-inline-end: 0px;
    border-inline-start: 0px;
    background: var(--v-pos-shell-background);
  }
  .period-text{
    padding: 2px;
    margin-inline-start: 20px;
  }
  .v-list-item:last-child{
    border-bottom: 0px !important;
  }
</style>