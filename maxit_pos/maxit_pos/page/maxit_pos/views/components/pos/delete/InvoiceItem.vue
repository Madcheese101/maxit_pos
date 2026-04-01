<template>
    <!-- <v-row> -->
        <v-col>{{ props.item.item_code }}</v-col>
        <v-col>{{ props.item.qty }} x {{ props.item.rate }}</v-col>
        <v-col>{{ props.item.amount }}</v-col>
    <!-- </v-row> -->
</template>
<script setup>
    const props = defineProps(['item']);
</script>