<template>
    <!-- <v-text-field
        append-inner-icon="mdi-magnify"
        density="compact"
        label="Search templates"
        variant="solo"
        hide-details
        single-line
        @click:append-inner="onClick"
    ></v-text-field> -->
    <v-row height="50" dense>
        <!-- Search bar -->
        <v-col cols="4">
            <div >
                <v-text-field
                    density="compact"
                    :placeholder="frappeRef._('Search')"
                    prepend-inner-icon="mdi-magnify"
                    variant="solo"
                    flat
                    hide-details
                    single-line
                ></v-text-field>
            </div>
        </v-col>
        <!-- item group filter -->
        <v-col cols="3">
            <v-select
                    :label="frappeRef._('Item Group')"
                    :items="item_groups"
                    variant="solo"
                    density="compact"
                    bg-color="white"
                    flat>
                </v-select>
        </v-col>
        <!-- more filters -->
        <v-col cols="2">
            <v-btn
                color="white"
                density="comfortable"
                append-icon="mdi-filter"
                height="40"
                flat
                :disabled="props.customFilters.length === 0"
                @click="showFiltersDialog()">
                    {{ frappeRef._('Filter') }}{{ active_filters > 0 ? ` (${active_filters})` : '' }}
            </v-btn>
        </v-col>
    </v-row>

</template>

<script setup>
    import { ref, toRefs, computed } from 'vue';
    import _ from "lodash";

    const props = defineProps(['customFilters']);
    const frappeRef = ref(frappe);
    const item_groups = ref([__("all")]);
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

    const applyFilters = (filter_values) => {
        // showDialog.value = false;
        active_filters.value = Object.keys(filter_values).length;

        filters.value.forEach(dict => {
            if(filter_values[dict.fieldname]){
                dict.selected = filter_values[dict.fieldname];
            }
        });
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

    get_filters();

</script>