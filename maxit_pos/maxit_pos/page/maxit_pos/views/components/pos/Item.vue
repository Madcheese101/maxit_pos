<template>
    <v-card rounded="lg" variant="flat" class="item-card">
        <v-img
            v-if="props.item.item_image"
            :src="props.item.item_image"
            :alt="props.item.item_name"
            height="88"
            cover
        ></v-img>

        <div class="item-card__body" :title="props.item.item_name">
            <div class="item-card__name">{{ props.item.item_name }}</div>
            <div class="item-card__meta">
                <span class="item-card__price">
                    {{ props.item.price_list_rate }}
                    <span class="item-card__unit">{{ props.item.currency || '' }} / {{ props.item.uom }}</span>
                </span>
                <span
                    class="item-card__stock"
                    :class="props.item.actual_qty > 0 ? 'text-success' : 'text-error'"
                >
                    {{ props.item.actual_qty }}
                </span>
            </div>
        </div>
    </v-card>
</template>
<script setup>
    const props = defineProps(['item']);
</script>

<style scoped>
    .item-card {
        display: flex;
        flex-direction: column;
        border: 1px solid var(--v-pos-panel-border-soft);
        background: var(--v-pos-panel-background);
        transition: var(--v-theme-transition);
    }

    .item-card__body {
        display: flex;
        flex-direction: column;
        justify-content: space-between;
        gap: 6px;
        flex: 1;
        min-height: 72px;
        padding: 8px 10px;
    }

    .item-card__name {
        display: -webkit-box;
        -webkit-line-clamp: 3;
        -webkit-box-orient: vertical;
        overflow: hidden;
        font-size: 0.875rem;
        font-weight: 600;
        line-height: 1.35;
        color: rgb(var(--v-theme-on-surface));
    }

    .item-card__meta {
        display: flex;
        align-items: baseline;
        justify-content: space-between;
        gap: 6px;
    }

    .item-card__price {
        font-size: 0.875rem;
        font-weight: 700;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
    }

    .item-card__unit {
        font-size: 0.72rem;
        font-weight: 500;
        color: rgb(var(--v-pos-text-muted));
    }

    .item-card__stock {
        flex-shrink: 0;
        font-size: 0.75rem;
        font-weight: 700;
    }
</style>
