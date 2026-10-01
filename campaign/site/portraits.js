/* Portraits for the campaign's characters, keyed by entity id, for upstream's sheet header
   (system/l5r5e/sheet.js reads window.L5RPortraits). Presentation, not game data: the same images
   the retired play/ sheets showed (campaign/PLAN.md M4). Tonbo Kuma has none. */
window.L5RPortraits = Object.assign(window.L5RPortraits || {}, {
  '#FPpcDojiSetsuna': 'campaign/assets/setsuna.webp',
  '#FPpcShinjoHarunobu': 'campaign/assets/harunobu.webp',
  '#FPpcAsahinaJujiro': 'campaign/assets/jujiro.webp',
  '#FPpcShinjoAnzu': 'campaign/assets/anzu.webp',
  '#FPpcMatsuMorozane': 'campaign/assets/morozane.webp',
});
