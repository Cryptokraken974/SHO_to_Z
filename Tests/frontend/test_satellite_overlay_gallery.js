const fs = require('fs');
const path = require('path');
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

const rootDir = path.resolve(__dirname, '../..');
const modularGalleryCode = fs.readFileSync(path.join(rootDir, 'frontend/js/modular-gallery.js'), 'utf8');
vm.runInContext(modularGalleryCode, context);
const satCode = fs.readFileSync(path.join(rootDir, 'frontend/js/satellite-overlay-gallery.js'), 'utf8');
context.satellite = () => ({ getSentinel2Overlay: async () => ({ image_data: 'AA==' }) });
context.window.UIManager = { addSentinel2OverlayToMap: () => {} };
vm.runInContext(satCode, context);

let added = null;
const gallery = new context.window.SatelliteOverlayGallery('satellite-gallery', {
  onAddToMap: (rb) => { added = rb; }
});

gallery.showImages([{ id: 'region_test_RED_B04', imageUrl: 'img.png', title: 'Red', bandType: 'Red' }]);
assert(container.innerHTML.includes('img.png'), 'renders image');

gallery.gallery.options.onAddToMap('region_test_RED_B04');
assert.strictEqual(added, 'region_test_RED_B04');

console.log('SatelliteOverlayGallery tests passed');
