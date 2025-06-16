const fs = require('fs');
const path = require('path');
const vm = require('vm');
const assert = require('assert');

const code = fs.readFileSync(path.join(__dirname, '../../frontend/js/geotiff-left-panel.js'), 'utf8');
const wrapper = `(function(){ ${code}; return GeoTiffLeftPanel; })()`;
const GeoTiffLeftPanel = vm.runInNewContext(wrapper, { window: {}, document: { addEventListener: () => {}, getElementById: () => null, querySelectorAll: () => [] } });

const files = [
  { name: 'a.laz', webkitRelativePath: 'folder1/a.laz' },
  { name: 'b.laz', webkitRelativePath: 'folder1/b.laz' },
  { name: 'c.laz', webkitRelativePath: 'folder2/c.laz' },
  { name: 'readme.txt', webkitRelativePath: 'folder2/readme.txt' }
];

const counts = GeoTiffLeftPanel.countLazFilesByFolder(files);
const plain = JSON.parse(JSON.stringify(counts));
assert.deepStrictEqual(plain, { folder1: 2, folder2: 1 });

console.log('LAZ folder count tests passed');
