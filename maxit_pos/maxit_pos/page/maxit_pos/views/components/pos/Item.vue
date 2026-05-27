<template>
    <v-card rounded="lg" class="ma-auto item-card">
        <!-- Image with the chip -->
        <!-- <v-card-item class="d-flex justify-space-between"> -->
            <v-img
                :src=" props.item.item_image || 'https://operaparallele.org/wp-content/uploads/2023/09/Placeholder_Image.png'"
                alt="Item Image"
                gradient="to bottom, rgba(0,0,0,0), rgba(0,0,0,0.4)"
                height="150px"></v-img>
            <v-chip
                :color="props.item.actual_qty > 0 ? 'success' : 'error'"
                variant="tonal"
                class="position-absolute top-0 mt-2 stock-chip"
            >
            {{ props.item.actual_qty }}
            </v-chip>
        <!-- </v-card-item> -->

        <!-- Item Details -->
        <v-card-title>
            <h5 class="m-0 item-title">{{ props.item.item_name }}</h5>
        </v-card-title>
        <v-card-subtitle>
            <h5 class="mt-0 item-subtitle">{{ props.item.price_list_rate }} {{ props.item.currency || '' }} / {{ props.item.uom }}</h5>
        </v-card-subtitle>
    </v-card>
</template>
<script setup>
    const props = defineProps(['item']);
</script>

<style scoped>
    .item-card {
        border: 1px solid var(--v-pos-panel-border-soft);
        background: var(--v-pos-panel-background);
        box-shadow: var(--v-pos-panel-shadow);
        transition: var(--v-theme-transition);
    }

    .stock-chip {
        inset-inline-end: 8px;
    }

    .item-title {
        color: rgb(var(--v-theme-on-surface));
    }

    .item-subtitle {
        color: rgb(var(--v-pos-text-muted));
    }
</style>