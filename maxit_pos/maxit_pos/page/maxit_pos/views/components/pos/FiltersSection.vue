<template>
    <v-row height="70" dense>
        <!-- Search bar -->
        <v-col cols="4">
            <div >
                <v-text-field
                    density="compact"
                    :placeholder="frappeRef._('Search')"
                    prepend-inner-icon="mdi-magnify"
                    variant="outlined"
                    hide-details
                    single-line
                    v-model="search_term"
                    @keydown.enter="emit_get_items"
                ></v-text-field>
            </div>
        </v-col>
        <!-- item group filter -->
        <v-col cols="3">
            <v-select
                :label="frappeRef._('Item Group')"
                v-model="selectedItemGroup"
                :items="item_groups"
                variant="outlined"
                density="compact"
                flat>
            </v-select>
        </v-col>
        <!-- more filters -->
        <v-col max-width="140" v-if="props.customFilters.length > 0">
            <v-btn
                color="primary"
                density="comfortable"
                append-icon="mdi-filter"
                height="40"
                variant="tonal"
                @click="showFiltersDialog()">
                    {{ frappeRef._('Filter') }}{{ active_filters > 0 ? ` (${active_filters})` : '' }}
            </v-btn>
            <!-- reset filters Button -->
            <v-btn  v-if="active_filters > 0"
                color="error"
                density="comfortable"
                icon="mdi-filter-remove"
                class="ml-2"
                @click="reset_filters()"
                variant="tonal"></v-btn>
                
        </v-col>
    </v-row>

</template>

<script setup>
    import { ref, toRefs, computed, watch} from 'vue';
    import _ from "lodash";
    const emit = defineEmits(['GetItems']);
    const props = defineProps(['customFilters', 'allowedItemGroups', 'posProfile']);
    const frappeRef = ref(frappe);
    const search_term = ref('');
    const item_groups = ref([__("all")]);
    const selectedItemGroup = ref(__("all"))
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
            primary_action_label: 'Submit',
            primary_action(values) {
                applyFilters(values);
                d.hide();
            }
        });

        d.show();
    }

    const emit_get_items = () => {
        const item_group = selectedItemGroup.value === __("all") 
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