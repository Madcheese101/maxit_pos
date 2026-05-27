<template>
  <v-dialog
    :model-value="modelValue"
    max-width="420"
    @update:model-value="emit('update:modelValue', $event)"
  >
    <v-card class="settings-dialog" rounded="xl">
      <v-card-item class="pb-2">
        <v-card-title class="text-h6">{{ __('Settings') }}</v-card-title>
      </v-card-item>

      <v-divider />

      <v-card-text class="pt-4">
        <v-select
          v-model="language"
          :items="languageOptions"
          :label="__('Language')"
          item-title="label"
          item-value="value"
          variant="outlined"
        />

        <v-select
          v-model="theme"
          :items="themeOptions"
          :label="__('Theme')"
          item-title="label"
          item-value="value"
          variant="outlined"
        />
      </v-card-text>

      <v-card-actions class="px-6 pb-4">
        <v-spacer />
        <v-btn variant="text" :disabled="isSaving" @click="closeDialog">{{ __('Cancel') }}</v-btn>
        <v-btn color="primary" :loading="isSaving" @click="saveSettings">{{ __('Save') }}</v-btn>
      </v-card-actions>
    </v-card>
  </v-dialog>
</template>

<script setup>
  import { computed, ref, watch } from 'vue';

  const __ = window.__;

  const props = defineProps({
    modelValue: {
      type: Boolean,
      default: false,
    },
    initialLanguage: {
      type: String,
      default: 'en',
    },
    initialTheme: {
      type: String,
      default: 'light',
    },
    isSaving: {
      type: Boolean,
      default: false,
    },
  });

  const emit = defineEmits(['update:modelValue', 'save']);

  const normalizeLanguage = (value) => {
    return String(value || 'en').toLowerCase().startsWith('ar') ? 'ar' : 'en';
  };

  const language = ref(normalizeLanguage(props.initialLanguage));
  const theme = ref(props.initialTheme || 'light');

  const languageOptions = computed(() => [
    { label: __('English'), value: 'en' },
    { label: __('Arabic'), value: 'ar' },
  ]);

  const themeOptions = computed(() => [
    { label: __('Light'), value: 'light' },
    { label: __('Dark'), value: 'dark' },
  ]);

  const syncFormState = () => {
    language.value = normalizeLanguage(props.initialLanguage);
    theme.value = props.initialTheme || 'light';
  };

  watch(
    () => props.modelValue,
    (isOpen) => {
      if (isOpen) {
        syncFormState();
      }
    }
  );

  watch(
    () => props.initialTheme,
    (value) => {
      if (!props.modelValue) {
        theme.value = value || 'light';
      }
    }
  );

  watch(
    () => props.initialLanguage,
    (value) => {
      if (!props.modelValue) {
        language.value = normalizeLanguage(value);
      }
    }
  );

  const closeDialog = () => {
    emit('update:modelValue', false);
  };

  const saveSettings = () => {
    emit('save', {
      language: language.value,
      theme: theme.value,
    });
  };
</script>

<style scoped>
  .settings-dialog {
    overflow: hidden;
  }
</style>