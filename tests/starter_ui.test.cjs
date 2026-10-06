const { test } = require('node:test');
const assert = require('node:assert/strict');
const { readFileSync } = require('node:fs');
const vm = require('node:vm');

test('starter correlates host replies, ignores other frames and recovers from errors/timeouts', () => {
  const handlers = {};
  const button = { disabled: false, addEventListener: (kind, fn) => handlers[kind] = fn };
  const output = { textContent: '' };
  const name = { value: '<Developer>' };
  const form = { querySelector: () => button, addEventListener: (kind, fn) => handlers[kind] = fn };
  let sent, timeout;
  const parent = { postMessage: (data) => sent = data };
  const tokens = {};
  const style = {setProperty: (key, value) => tokens[key] = value};
  const context = { parent, document: { documentElement: {style}, getElementById: id => ({greeting: form, result: output, name})[id] },
    window: { addEventListener: (kind, fn) => handlers[kind] = fn },
    crypto: { getRandomValues: values => values.fill(42) }, Uint32Array, setTimeout: fn => timeout = fn, clearTimeout: () => {} };
  vm.runInNewContext(readFileSync(process.argv[2], 'utf8'), context);
  assert.equal(sent.method, 'plugin.theme');
  handlers.message({source: {}, data: {type: 'plugin-appearance-changed', appearance: {mode: 'dark', tokens: {'--ui-bg': 'purple'}}}});
  assert.deepEqual(tokens, {});
  handlers.message({source: parent, data: {type: 'plugin-api-response', requestId: sent.requestId, result: {mode: 'dark', tokens: {'--ui-bg': 'purple', '--bad': 'red'}}}});
  assert.equal(tokens['--ui-bg'], 'purple');
  assert.equal(tokens['--bad'], undefined);
  assert.equal(style.colorScheme, 'dark');
  handlers.message({source: parent, data: {type: 'plugin-appearance-changed', appearance: {mode: 'light', tokens: {'--ui-bg': 'green'}}}});
  assert.equal(tokens['--ui-bg'], 'green');
  assert.equal(style.colorScheme, 'light');
  handlers.click();
  assert.equal(sent.method, 'plugin.run-action');
  assert.equal(sent.payload.values.name, '<Developer>');
  assert.equal(button.disabled, true);
  const response = { type: 'plugin-api-response', requestId: sent.requestId, result: {message: 'Hello, <Developer>!'} };
  handlers.message({ source: {}, data: response });
  handlers.message({ source: parent, data: {...response, requestId: 'stale'} });
  assert.equal(button.disabled, true);
  handlers.message({ source: parent, data: response });
  assert.equal(output.textContent, 'Hello, <Developer>!');
  assert.equal(button.disabled, false);
  handlers.click();
  handlers.message({ source: parent, data: {...response, error: 'Permission denied'} });
  assert.equal(output.textContent, 'Permission denied');
  handlers.click();
  timeout();
  assert.equal(button.disabled, false);
  assert.match(output.textContent, /did not respond/);
});
