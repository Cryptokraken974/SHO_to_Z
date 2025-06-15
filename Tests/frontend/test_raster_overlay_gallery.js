const fs = require('fs');
const vm = require('vm');
const assert = require('assert');

// Minimal DOM stub
const container = {
  innerHTML: '',
  classList: { add() {} },
  addEventListener(event, handler) { this.handler = handler; },
  querySelectorAll() { return []; }
};

const context = {
  window: {},
  document: { getElementById: () => container }
};
vm.createContext(context);

const modularGalleryCode = fs.readFileSync('frontend/js/modular-gallery.js', 'utf8');
vm.runInContext(modularGalleryCode, context);
const rasterCode = fs.readFileSync('frontend/js/raster-overlay-gallery.js', 'utf8');
context.overlays = () => ({ getRasterOverlayData: async () => ({ image_data: 'AA==' }) });
context.window.UIManager = { getProcessingDisplayName: (t) => t };
vm.runInContext(rasterCode, context);

let added = null;
const gallery = new context.window.RasterOverlayGallery('raster-overlay-gallery', {
  onAddToMap: (pt) => { added = pt; }
});

gallery.showRasters([{ id: 'hs_red', imageUrl: 'img.png', title: 'HS' }]);
assert(container.innerHTML.includes('img.png'), 'renders image');

gallery.gallery.options.onAddToMap('hs_red');
assert.strictEqual(added, 'hs_red');

console.log('RasterOverlayGallery tests passed');
