<template>
    <v-card color="#edf2f5" rounded="lg" class="ma-auto">
        <!-- Image with the chip -->
        <!-- <v-card-item class="d-flex justify-space-between"> -->
            <v-img
                :src=" props.item.item_image || 'https://operaparallele.org/wp-content/uploads/2023/09/Placeholder_Image.png'"
                alt="Item Image"
                gradient="to bottom, rgba(0,0,0,0), rgba(0,0,0,0.4)"
                height="150px"></v-img>
            <v-chip
                :color="props.item.actual_qty > 0 ? '#e4f5e9' : '#fff0f0'"
                variant="flat"
                class="position-absolute top-0 mt-2 stock-chip"
            >
            {{ props.item.actual_qty }}
            </v-chip>
        <!-- </v-card-item> -->

        <!-- Item Details -->
        <v-card-title>
            <h5 class="m-0 text-grey-darken-4">{{ props.item.item_name }}</h5>
        </v-card-title>
        <v-card-subtitle>
            <h5 class="mt-0 text-grey-darken-4">{{ props.item.price_list_rate }} {{ props.item.currency || '' }} / {{ props.item.uom }}</h5>
        </v-card-subtitle>
    </v-card>
</template>
<script setup>
    const props = defineProps(['item']);
</script>

<style scoped>
    .stock-chip {
        inset-inline-end: 8px;
    }
</style>