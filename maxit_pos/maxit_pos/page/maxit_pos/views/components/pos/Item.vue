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
                :color="props.item.qty > 0 ? '#e4f5e9' : '#fff0f0'"
                variant="flat"
                class="position-absolute top-0 right-0 mr-2 mt-2"
            >
            {{ props.item.qty }}
            </v-chip>
        <!-- </v-card-item> -->

        <!-- Item Details -->
        <v-card-title>
            <h4 class="m-0">{{ props.item.item_name }}</h4>
        </v-card-title>
        <v-card-subtitle>
            <h5 class="mt-0">{{ props.item.item_price }} / {{ props.item.uom }}</h5>
        </v-card-subtitle>
    </v-card>
</template>
<script setup>
    const props = defineProps(['item']);

    const itemQuantity = 0; // Replace with your actual quantity
    const itemName = "Sneakers"; // Replace with your actual item name
    const itemPrice = "100 AED"; // Replace with your actual item price
</script>