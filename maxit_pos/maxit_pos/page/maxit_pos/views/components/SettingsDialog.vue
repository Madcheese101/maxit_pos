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

      <v-card-text>
        <v-select
          v-model="language"
          :items="languageOptions"
          :label="__('Language')"
          item-title="label"
          item-value="value"
          variant="outlined"
        />

        <v-select
          class="mt-3"
          v-model="theme"
          :items="themeOptions"
          :label="__('Theme')"
          item-title="label"
          item-value="value"
          variant="outlined"
        />

        <v-select
          v-if="theme === 'dark'"
          v-model="darkPalette"
          :items="darkPaletteOptions"
          :label="__('Dark Palette')"
          item-title="label"
          item-value="value"
          variant="outlined"
          class="mt-3"
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
  import { DARK_PALETTES, normalizeDarkPalette, normalizeThemeMode } from '../../themeConfig';

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
    initialDarkPalette: {
      type: String,
      default: DARK_PALETTES.SLATE,
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
  const theme = ref(normalizeThemeMode(props.initialTheme));
  const darkPalette = ref(normalizeDarkPalette(props.initialDarkPalette));

  const languageOptions = computed(() => [
    { label: __('English'), value: 'en' },
    { label: __('Arabic'), value: 'ar' },
  ]);

  const themeOptions = computed(() => [
    { label: __('Light'), value: 'light' },
    { label: __('Dark'), value: 'dark' },
  ]);

  const darkPaletteOptions = computed(() => [
    { label: __('Slate and steel blue'), value: DARK_PALETTES.SLATE },
    { label: __('Charcoal and emerald'), value: DARK_PALETTES.EMERALD },
    { label: __('Graphite and amber'), value: DARK_PALETTES.AMBER },
  ]);

  const syncFormState = () => {
    language.value = normalizeLanguage(props.initialLanguage);
    theme.value = normalizeThemeMode(props.initialTheme);
    darkPalette.value = normalizeDarkPalette(props.initialDarkPalette);
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
        theme.value = normalizeThemeMode(value);
      }
    }
  );

  watch(
    () => props.initialDarkPalette,
    (value) => {
      if (!props.modelValue) {
        darkPalette.value = normalizeDarkPalette(value);
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
      darkPalette: darkPalette.value,
    });
  };
</script>

<style scoped>
  .settings-dialog {
    overflow: hidden;
    border: 1px solid var(--v-pos-panel-border);
    background: var(--v-pos-panel-background);
    box-shadow: var(--v-pos-panel-shadow-strong);
    transition: var(--v-theme-transition);
  }
</style>