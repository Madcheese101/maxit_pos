import {defineStore} from "pinia"
import {ref} from "vue"

export const usePosStore = defineStore('posStore', () => {
    // states
    const posProfileData = ref({});
    const pos_opening = ref("");
    const company = ref("");
    const pos_profile = ref("");
    const pos_opening_time = ref();
    const item_stock_map = ref();
    const allow_negative_stock = ref(false);
    const customer_groups = ref([]);

    // actions
    const setAppDefaults = (posProfile, appDefaults) => {
        posProfileData.value = posProfile;
        pos_opening.value = appDefaults.pos_opening;
        company.value = appDefaults.company;
        pos_profile.value = appDefaults.pos_profile;
        pos_opening_time.value = appDefaults.pos_opening_time;
        item_stock_map.value = appDefaults.item_stock_map;
        allow_negative_stock.value = appDefaults.allow_negative_stock;
        customer_groups.value = appDefaults.customer_groups;
    }

    return {
        // states
        
        posProfileData,
        pos_profile,
        // company,
        // pos_opening,
        // pos_opening_time,
        // item_stock_map,
        // allow_negative_stock,
        // customer_groups,

        // actions
        setAppDefaults
    }
})