const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');

const root = path.join(__dirname, '..');
const client = fs.readFileSync(path.join(root, 'Client.html'), 'utf8');
const clientScript = client.match(/<script>([\s\S]*?)<\/script>/)[1];

function renderClient(params, search = '') {
  let onReady;
  const routes = [];
  const document = {
    addEventListener(type, listener) { if (type === 'DOMContentLoaded') onReady = listener; },
    getElementById() { return { innerHTML: '', hidden: false, value: '', focus() {} }; }
  };
  const context = vm.createContext({
    document,
    window: params === undefined ? {} : { SSLG_SERVER_PARAMS: params },
    location: { search },
    URLSearchParams
  });
  vm.runInContext(clientScript, context, { filename: 'Client.html' });
  context.renderAdminPage_ = () => routes.push('admin');
  context.renderLandingPage_ = () => routes.push('landing');
  context.renderScanPage_ = params => routes.push({ scan: JSON.parse(JSON.stringify(params)) });
  onReady();
  return { context, routes };
}

function renderedServer(event) {
  const context = vm.createContext({
    HtmlService: { createHtmlOutput: html => ({ getContent: () => html }) }
  });
  context.HtmlService.createTemplateFromFile = name => {
    assert.equal(name, 'Index');
    return {
      evaluate() {
        return {
          setTitle() { return this; },
          getContent() {
            const index = fs.readFileSync(path.join(root, 'Index.html'), 'utf8');
            return index.replace(/<\?!= ([A-Za-z_]+)\(event\); \?>/, (_, functionName) => context[functionName](event));
          }
        };
      }
    };
  };
  for (const file of ['Core.gs', 'Code.gs']) {
    vm.runInContext(fs.readFileSync(path.join(root, file), 'utf8'), context, { filename: file });
  }
  return context.doGet(event).getContent();
}

test('doGet injects scan parameters into the sandboxed page', () => {
  const html = renderedServer({ parameter: { page: 'scan', mode: 'IN', code: 'permanent-in', ignored: 'secret' } });
  const match = html.match(/window\.SSLG_SERVER_PARAMS = (.*?);<\/script>/);
  assert.ok(match, 'server parameters are present in the page');
  assert.deepEqual(JSON.parse(match[1]), { page: 'scan', mode: 'IN', code: 'permanent-in' });
});

test('doGet safely escapes script-breaking query values', () => {
  const html = renderedServer({ parameter: { page: '</script><script>alert(1)</script>&\u2028\u2029' } });
  const match = html.match(/window\.SSLG_SERVER_PARAMS = (.*?);<\/script>/);
  assert.ok(match);
  assert.doesNotMatch(html, /<script>alert\(1\)<\/script>/);
  assert.doesNotMatch(match[1], /<\/script>|&|\u2028|\u2029/);
  assert.equal(JSON.parse(match[1]).page, '</script><script>alert(1)</script>&\u2028\u2029');
});

test('client routes using server parameters when the sandbox URL has no query', () => {
  const { routes } = renderClient({ page: 'admin' });
  assert.deepEqual(routes, ['admin']);
});

test('client reads scan mode and code from server parameters', () => {
  const { context, routes } = renderClient({ page: 'scan', mode: 'OUT', code: 'permanent-out' });
  assert.deepEqual(routes, [{ scan: { mode: 'OUT', code: 'permanent-out' } }]);
  assert.deepEqual(JSON.parse(JSON.stringify(context.scanParams_())), { mode: 'OUT', code: 'permanent-out' });
});

test('client retains query-string routing for the local preview', () => {
  const { routes } = renderClient(undefined, '?page=scan&mode=IN&code=preview-in');
  assert.deepEqual(routes, [{ scan: { mode: 'IN', code: 'preview-in' } }]);
});

test('empty server parameters fall back to the preview query string', () => {
  const { routes } = renderClient({}, '?page=admin');
  assert.deepEqual(routes, ['admin']);
});
