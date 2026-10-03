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
  const context = { parent, document: { getElementById: id => ({greeting: form, result: output, name})[id] },
    window: { addEventListener: (kind, fn) => handlers[kind] = fn },
    crypto: { getRandomValues: values => values.fill(42) }, Uint32Array, setTimeout: fn => timeout = fn, clearTimeout: () => {} };
  vm.runInNewContext(readFileSync(process.argv[2], 'utf8'), context);
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
