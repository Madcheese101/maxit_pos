<template>
	<v-date-input
		:model-value="toDate(modelValue)"
		:display-format="formatDate"
		:placeholder="placeholder"
		prepend-icon=""
		prepend-inner-icon="$calendar"
		variant="outlined"
		density="compact"
		hide-actions
		v-bind="$attrs"
		@update:model-value="emit('update:modelValue', toDateString($event))"
	/>
</template>

<script setup>
	// Vuetify date picker that keeps the value as a Frappe date string (YYYY-MM-DD)
	// and shows it in the user's date format, instead of the browser's native date input.
	defineOptions({ inheritAttrs: false });

	defineProps({
		modelValue: {
			type: String,
			default: '',
		},
	});

	const emit = defineEmits(['update:modelValue']);
	const placeholder = window.frappe?.boot?.sysdefaults?.date_format || '';

	// parse as a local date; new Date('YYYY-MM-DD') would be UTC midnight
	function toDate(value) {
		if (!value) {
			return null;
		}

		const [year, month, day] = value.split('-').map(Number);
		return new Date(year, month - 1, day);
	}

	function toDateString(date) {
		if (!date) {
			return '';
		}

		const value = new Date(date);
		const pad = (number) => String(number).padStart(2, '0');
		return `${value.getFullYear()}-${pad(value.getMonth() + 1)}-${pad(value.getDate())}`;
	}

	function formatDate(date) {
		return window.frappe.datetime.str_to_user(toDateString(date));
	}
</script>
