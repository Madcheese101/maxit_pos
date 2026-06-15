export const THEME_MODES = Object.freeze({
  LIGHT: 'light',
  DARK: 'dark',
});

export const DARK_PALETTES = Object.freeze({
  SLATE: 'slate',
  EMERALD: 'emerald',
  AMBER: 'amber',
});

export const DEFAULT_THEME_MODE = THEME_MODES.LIGHT;
export const DEFAULT_DARK_PALETTE = DARK_PALETTES.SLATE;

export const THEME_MODE_STORAGE_KEY = 'maxit_pos_theme_mode';
export const DARK_PALETTE_STORAGE_KEY = 'maxit_pos_dark_palette';

export const VUETIFY_THEME_NAMES = Object.freeze({
  LIGHT: 'maxit-light',
  DARK_SLATE: 'maxit-dark-slate',
  DARK_EMERALD: 'maxit-dark-emerald',
  DARK_AMBER: 'maxit-dark-amber',
});

export const DARK_PALETTE_VALUES = Object.freeze(Object.values(DARK_PALETTES));

const themeVariables = ({
  shellBackground,
  drawerBackground,
  panelBackground,
  panelBorder,
  panelBorderSoft,
  panelBorderStrong,
  panelShadow,
  panelShadowStrong,
  navActive,
  navHover,
  avatarBackground,
  fieldBackground,
  successGlow,
  warningGlow,
  infoGlow,
  textMuted,
}) => ({
  'pos-shell-background': shellBackground,
  'pos-drawer-background': drawerBackground,
  'pos-panel-background': panelBackground,
  'pos-panel-border': panelBorder,
  'pos-panel-border-soft': panelBorderSoft,
  'pos-panel-border-strong': panelBorderStrong,
  'pos-panel-shadow': panelShadow,
  'pos-panel-shadow-strong': panelShadowStrong,
  'pos-nav-active': navActive,
  'pos-nav-hover': navHover,
  'pos-avatar-background': avatarBackground,
  'pos-field-background': fieldBackground,
  'pos-success-glow': successGlow,
  'pos-warning-glow': warningGlow,
  'pos-info-glow': infoGlow,
  'pos-text-muted': textMuted,
  'theme-transition': 'background 0.24s ease, color 0.24s ease, border-color 0.24s ease, box-shadow 0.24s ease',
});

export const normalizeThemeMode = (value) => {
  return value === THEME_MODES.DARK ? THEME_MODES.DARK : DEFAULT_THEME_MODE;
};

export const normalizeDarkPalette = (value) => {
  return DARK_PALETTE_VALUES.includes(value) ? value : DEFAULT_DARK_PALETTE;
};

export const resolveVuetifyThemeName = (mode = DEFAULT_THEME_MODE, darkPalette = DEFAULT_DARK_PALETTE) => {
  if (normalizeThemeMode(mode) !== THEME_MODES.DARK) {
    return VUETIFY_THEME_NAMES.LIGHT;
  }

  switch (normalizeDarkPalette(darkPalette)) {
    case DARK_PALETTES.EMERALD:
      return VUETIFY_THEME_NAMES.DARK_EMERALD;
    case DARK_PALETTES.AMBER:
      return VUETIFY_THEME_NAMES.DARK_AMBER;
    default:
      return VUETIFY_THEME_NAMES.DARK_SLATE;
  }
};

const userScopedKey = (key) => {
  const user = frappe?.session?.user || 'guest';
  return `${key}__${user}`;
};

const readStorageValue = (key) => {
  try {
    return window.localStorage.getItem(userScopedKey(key));
  } catch (error) {
    return null;
  }
};

export const readStoredThemePreferences = () => {
  return {
    mode: normalizeThemeMode(readStorageValue(THEME_MODE_STORAGE_KEY)),
    darkPalette: normalizeDarkPalette(readStorageValue(DARK_PALETTE_STORAGE_KEY)),
  };
};

export const persistThemePreferences = ({ mode, darkPalette }) => {
  const normalizedPreferences = {
    mode: normalizeThemeMode(mode),
    darkPalette: normalizeDarkPalette(darkPalette),
  };

  try {
    window.localStorage.setItem(userScopedKey(THEME_MODE_STORAGE_KEY), normalizedPreferences.mode);
    window.localStorage.setItem(userScopedKey(DARK_PALETTE_STORAGE_KEY), normalizedPreferences.darkPalette);
  } catch (error) {
    return normalizedPreferences;
  }

  return normalizedPreferences;
};

export const resolveInitialVuetifyTheme = () => {
  const { mode, darkPalette } = readStoredThemePreferences();
  return resolveVuetifyThemeName(mode, darkPalette);
};

export const vuetifyThemes = Object.freeze({
  [VUETIFY_THEME_NAMES.LIGHT]: {
    dark: false,
    colors: {
      background: '#edf2f5',
      surface: '#ffffff',
      primary: '#3559b7',
      secondary: '#60748b',
      success: '#2e7d32',
      warning: '#b7791f',
      error: '#c1445e',
      info: '#2b6cb0',
      'surface-variant': '#f3f7fb',
      'on-surface-variant': '#5f6f81',
      outline: '#b7c4d1',
      'outline-variant': '#d4dde6',
      'on-background': '#152235',
      'on-surface': '#152235',
      'on-primary': '#ffffff',
      'on-secondary': '#ffffff',
      'on-success': '#ffffff',
      'on-warning': '#ffffff',
      'on-error': '#ffffff',
      'on-info': '#ffffff',
    },
    variables: themeVariables({
      shellBackground: '#edf2f5',
      drawerBackground: 'linear-gradient(180deg, rgba(255, 255, 255, 0.96), rgba(248, 251, 255, 0.98))',
      panelBackground: 'linear-gradient(180deg, rgba(255, 255, 255, 0.94), rgba(248, 251, 255, 0.97))',
      panelBorder: 'rgba(120, 144, 156, 0.24)',
      panelBorderSoft: 'rgba(120, 144, 156, 0.18)',
      panelBorderStrong: 'rgba(120, 144, 156, 0.28)',
      panelShadow: '0 10px 24px rgba(12, 28, 43, 0.08)',
      panelShadowStrong: '0 8px 20px rgba(12, 28, 43, 0.12)',
      navActive: 'rgba(53, 89, 183, 0.14)',
      navHover: 'rgba(53, 89, 183, 0.08)',
      avatarBackground: 'rgba(96, 116, 139, 0.14)',
      fieldBackground: 'rgba(255, 255, 255, 0.9)',
      successGlow: 'rgba(46, 125, 50, 0.09)',
      warningGlow: 'rgba(251, 140, 0, 0.08)',
      infoGlow: 'rgba(25, 118, 210, 0.09)',
      textMuted: '#5f6f81',
    }),
  },
  [VUETIFY_THEME_NAMES.DARK_SLATE]: {
    dark: true,
    colors: {
      background: '#0f1724',
      surface: '#162033',
      primary: '#7b9cff',
      secondary: '#8fa4bd',
      success: '#63b38d',
      warning: '#d9aa63',
      error: '#ef7a8a',
      info: '#63b3ed',
      'surface-variant': '#1c2940',
      'on-surface-variant': '#a1b3cb',
      outline: '#324158',
      'outline-variant': '#26354d',
      'on-background': '#edf4ff',
      'on-surface': '#edf4ff',
      'on-primary': '#0f1724',
      'on-secondary': '#0f1724',
      'on-success': '#0f1724',
      'on-warning': '#0f1724',
      'on-error': '#0f1724',
      'on-info': '#0f1724',
    },
    variables: themeVariables({
      shellBackground: 'radial-gradient(circle at top, rgba(124, 150, 210, 0.28), rgba(28, 42, 63, 0.9) 42%), #172438',
      drawerBackground: 'linear-gradient(180deg, rgba(18, 28, 43, 0.98), rgba(11, 19, 31, 0.99))',
      panelBackground: 'linear-gradient(180deg, rgba(22, 32, 51, 0.96), rgba(15, 24, 39, 0.99))',
      panelBorder: 'rgba(148, 163, 184, 0.2)',
      panelBorderSoft: 'rgba(148, 163, 184, 0.12)',
      panelBorderStrong: 'rgba(148, 163, 184, 0.28)',
      panelShadow: '0 14px 30px rgba(2, 8, 23, 0.42)',
      panelShadowStrong: '0 18px 34px rgba(2, 8, 23, 0.48)',
      navActive: 'rgba(123, 156, 255, 0.18)',
      navHover: 'rgba(123, 156, 255, 0.12)',
      avatarBackground: 'rgba(148, 163, 184, 0.18)',
      fieldBackground: 'rgba(255, 255, 255, 0.04)',
      successGlow: 'rgba(99, 179, 141, 0.16)',
      warningGlow: 'rgba(217, 170, 99, 0.15)',
      infoGlow: 'rgba(99, 179, 237, 0.16)',
      textMuted: '#a1b3cb',
    }),
  },
  [VUETIFY_THEME_NAMES.DARK_EMERALD]: {
    dark: true,
    colors: {
      background: '#101917',
      surface: '#162321',
      primary: '#79c5b1',
      secondary: '#98b9b1',
      success: '#7ed6a2',
      warning: '#d7b36f',
      error: '#ef8d93',
      info: '#78bdd6',
      'surface-variant': '#1d2d2b',
      'on-surface-variant': '#b0cbc5',
      outline: '#36504b',
      'outline-variant': '#28423d',
      'on-background': '#edf8f4',
      'on-surface': '#edf8f4',
      'on-primary': '#10201d',
      'on-secondary': '#10201d',
      'on-success': '#10201d',
      'on-warning': '#10201d',
      'on-error': '#10201d',
      'on-info': '#10201d',
    },
    variables: themeVariables({
      shellBackground: 'radial-gradient(circle at top, rgba(112, 204, 174, 0.28), rgba(25, 43, 40, 0.9) 44%), #15211f',
      drawerBackground: 'linear-gradient(180deg, rgba(20, 34, 31, 0.98), rgba(12, 21, 19, 0.99))',
      panelBackground: 'linear-gradient(180deg, rgba(22, 35, 33, 0.96), rgba(16, 27, 25, 0.99))',
      panelBorder: 'rgba(125, 158, 149, 0.21)',
      panelBorderSoft: 'rgba(125, 158, 149, 0.13)',
      panelBorderStrong: 'rgba(125, 158, 149, 0.3)',
      panelShadow: '0 14px 30px rgba(3, 10, 9, 0.42)',
      panelShadowStrong: '0 18px 34px rgba(3, 10, 9, 0.48)',
      navActive: 'rgba(121, 197, 177, 0.2)',
      navHover: 'rgba(121, 197, 177, 0.12)',
      avatarBackground: 'rgba(125, 158, 149, 0.2)',
      fieldBackground: 'rgba(255, 255, 255, 0.04)',
      successGlow: 'rgba(126, 214, 162, 0.16)',
      warningGlow: 'rgba(215, 179, 111, 0.15)',
      infoGlow: 'rgba(120, 189, 214, 0.16)',
      textMuted: '#b0cbc5',
    }),
  },
  [VUETIFY_THEME_NAMES.DARK_AMBER]: {
    dark: true,
    colors: {
      background: '#18130f',
      surface: '#231b16',
      primary: '#d5a86c',
      secondary: '#b7a08a',
      success: '#8ac09c',
      warning: '#e2b86c',
      error: '#f09682',
      info: '#8ab8d9',
      'surface-variant': '#2c231d',
      'on-surface-variant': '#d0c0b1',
      outline: '#4e4034',
      'outline-variant': '#3d3128',
      'on-background': '#fbf3ea',
      'on-surface': '#fbf3ea',
      'on-primary': '#1a1510',
      'on-secondary': '#1a1510',
      'on-success': '#1a1510',
      'on-warning': '#1a1510',
      'on-error': '#1a1510',
      'on-info': '#1a1510',
    },
    variables: themeVariables({
      shellBackground: 'radial-gradient(circle at top, rgba(231, 190, 132, 0.28), rgba(40, 31, 24, 0.9) 44%), #1f1812',
      drawerBackground: 'linear-gradient(180deg, rgba(34, 27, 21, 0.98), rgba(19, 15, 11, 0.99))',
      panelBackground: 'linear-gradient(180deg, rgba(35, 27, 22, 0.96), rgba(24, 18, 14, 0.99))',
      panelBorder: 'rgba(183, 160, 138, 0.21)',
      panelBorderSoft: 'rgba(183, 160, 138, 0.13)',
      panelBorderStrong: 'rgba(183, 160, 138, 0.3)',
      panelShadow: '0 14px 30px rgba(10, 7, 4, 0.42)',
      panelShadowStrong: '0 18px 34px rgba(10, 7, 4, 0.48)',
      navActive: 'rgba(213, 168, 108, 0.2)',
      navHover: 'rgba(213, 168, 108, 0.12)',
      avatarBackground: 'rgba(183, 160, 138, 0.2)',
      fieldBackground: 'rgba(255, 255, 255, 0.04)',
      successGlow: 'rgba(138, 192, 156, 0.16)',
      warningGlow: 'rgba(226, 184, 108, 0.15)',
      infoGlow: 'rgba(138, 184, 217, 0.16)',
      textMuted: '#d0c0b1',
    }),
  },
});