import { defineConfig, presetUno, presetAttributify, presetTypography } from 'unocss';

export default defineConfig({
  presets: [presetUno(), presetAttributify(), presetTypography()],
  theme: {
    colors: {
      primary: '#82b440',
      dark: '#2e3235',
    }
  },
  shortcuts: {
    card: 'p-4 bg-white rounded-xl shadow'
  }
});
