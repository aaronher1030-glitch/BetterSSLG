const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const jsQR = require('jsqr');
const { PNG } = require('pngjs');

const source = fs.readFileSync(path.join(__dirname, '..', 'QRCodeLib.html'), 'utf8');
const context = vm.createContext({});
vm.runInContext(source, context, { filename: 'QRCodeLib.html' });

function decodeQr(value) {
  const qr = context.qrcode(0, 'M');
  qr.addData(value);
  qr.make();
  const dataUrl = qr.createDataURL(8, 4);
  const png = PNG.sync.read(Buffer.from(dataUrl.split(',')[1], 'base64'));
  const decoded = jsQR(new Uint8ClampedArray(png.data), png.width, png.height);
  return decoded && decoded.data;
}

test('IN QR payload decodes exactly', () => {
  const value = 'https://script.test/exec?page=scan&mode=IN&code=in-token';
  assert.equal(decodeQr(value), value);
});

test('OUT QR payload decodes exactly', () => {
  const value = 'https://script.test/exec?page=scan&mode=OUT&code=out-token';
  assert.equal(decodeQr(value), value);
});
