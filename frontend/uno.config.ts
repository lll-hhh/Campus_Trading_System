import { defineConfig, presetUno, presetAttributify, presetTypography } from 'unocss';

export default defineConfig({
  presets: [presetUno(), presetAttributify(), presetTypography()],
  shortcuts: {
    card: 'p-4 bg-white rounded-xl shadow'
  }
});
