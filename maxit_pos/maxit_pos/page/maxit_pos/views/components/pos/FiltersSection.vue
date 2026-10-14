<template>
    <div class="filters-bar">
        <v-text-field
            class="filters-bar__search"
            density="compact"
            :placeholder="__('Search')"
            prepend-inner-icon="mdi-magnify"
            variant="outlined"
            hide-details
            single-line
            v-model="search_term"
            @keydown.enter="emit_get_items"
        ></v-text-field>
        <v-select
            class="filters-bar__group"
            :label="__('Item Group')"
            v-model="selectedItemGroup"
            :items="item_groups"
            variant="outlined"
            density="compact"
            hide-details
            flat>
        </v-select>
        <template v-if="props.customFilters.length > 0">
            <v-btn
                color="primary"
                variant="tonal"
                icon
                size="small"
                :aria-label="__('Filter')"
                :title="__('Filter')"
                @click="showFiltersDialog()">
                <v-badge v-if="active_filters > 0" :content="active_filters" color="primary" floating>
                    <v-icon icon="mdi-filter" />
                </v-badge>
                <v-icon v-else icon="mdi-filter" />
            </v-btn>
            <v-btn v-if="active_filters > 0"
                color="error"
                variant="tonal"
                icon="mdi-filter-remove"
                size="small"
                @click="reset_filters()"></v-btn>
        </template>
        <slot />
    </div>

</template>

<script setup>
    import { ref, watch} from 'vue';
    import _ from "lodash";
    const emit = defineEmits(['getItems']);
    const props = defineProps(['customFilters', 'allowedItemGroups', 'posProfile']);
    const __ = window.__;
    const search_term = ref('');
    const allItemGroupsLabel = __('all');
    const item_groups = ref([allItemGroupsLabel]);
    const selectedItemGroup = ref(allItemGroupsLabel)
    const showDialog = ref(false);
    const filters = ref([]);
    const active_filters = ref(0);

    const get_filters = () => {
        const length = props.customFilters.length
        if (length > 0) {
            frappe.call('maxit_pos.maxit_pos.page.maxit_pos.api.api.get_advanced_item_filters_dict', 
            {custom_filters: props.customFilters}).then((res) => {
                filters.value = res.message;
            });
        }
    }

    const get_item_groups = () => {
        // if (props.allowedItemGroups.length > 0) {
        //     props.allowedItemGroups.forEach(row => {
        //         item_groups.value.push(row.item_group);
        //     })
        //     return;
        // }
        frappe.call('maxit_pos.maxit_pos.page.maxit_pos.api.api.get_item_group_list', 
        {allowed_item_groups: props.allowedItemGroups, pos_profile: props.posProfile}).then((res) => {
            item_groups.value.push(...res.message);
        });
    }

    const applyFilters = (filter_values) => {
        // showDialog.value = false;
        // get the number of active filters
        active_filters.value = Object.keys(filter_values).length;

        filters.value.forEach(dict => {
            if(filter_values[dict.fieldname]){
                dict.selected = filter_values[dict.fieldname];
            }
        });
        emit_get_items();
    }

    const reset_filters = () => {
        filters.value.forEach(dict => {
            dict.selected = null;
        });
        active_filters.value = 0;
        emit_get_items();
    }
    
    const showFiltersDialog = () => {
        const custom_fields = [];

        filters.value.forEach((filter) => {
            custom_fields.push({
                label: filter.label,
                fieldname: filter.fieldname,
                fieldtype: filter.field_type,
                options: filter.field_type === "Link" ? filter.doctype : filter.options,
                default: filter.selected
            });
        });
        
        let d = new frappe.ui.Dialog({
            title: __('Set Filters'),
            fields: custom_fields,
            size: 'small', // small, large, extra-large 
            primary_action_label: __('Submit'),
            primary_action(values) {
                applyFilters(values);
                d.hide();
            }
        });

        d.show();
    }

    const emit_get_items = () => {
        const item_group = selectedItemGroup.value === allItemGroupsLabel 
            ? null : selectedItemGroup.value;

        emit('getItems', {
            search_term: search_term.value,
            item_group: item_group,
            filters: filters.value
        });
    }
    
    watch((selectedItemGroup), (newVal) => {
        emit_get_items();
    });

    get_filters();
    get_item_groups();

</script>

<style scoped>
    .filters-bar {
        display: flex;
        flex-wrap: wrap;
        align-items: center;
        gap: 8px;
        container-type: inline-size;
    }

    .filters-bar__search {
        flex: 2 1 160px;
    }

    .filters-bar__group {
        flex: 1 1 120px;
        max-width: 240px;
    }

    /* narrow panes: search gets its own row */
    @container (max-width: 480px) {
        .filters-bar__search {
            flex-basis: 100%;
        }

        .filters-bar__group {
            max-width: none;
        }
    }
</style>
