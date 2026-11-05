const test = require('node:test');
const assert = require('node:assert/strict');
const config = require('./api/donation/config');
const create = require('./api/donation/create');

function response() {
  return { headers: {}, setHeader(k, v) { this.headers[k] = v; },
    status(code) { this.code = code; return this; }, json(body) { this.body = body; return this; } };
}

test('payment API stays closed without all production settings', async () => {
  const old = process.env.GLANCE_DONATIONS_ENABLED;
  process.env.GLANCE_DONATIONS_ENABLED = 'false';
  const r = response(); config({ method: 'GET' }, r);
  assert.deepEqual(r.body, { enabled: false });
  const denied = response(); await create({ method: 'POST', headers: {} }, denied);
  assert.equal(denied.code, 503);
  if (old === undefined) delete process.env.GLANCE_DONATIONS_ENABLED; else process.env.GLANCE_DONATIONS_ENABLED = old;
});

test('creates a signed PayOS request and rejects other origins or invalid amounts', async t => {
  const snapshot = { ...process.env };
  const fetchBefore = global.fetch;
  t.after(() => { process.env = snapshot; global.fetch = fetchBefore; });
  Object.assign(process.env, { GLANCE_DONATIONS_ENABLED: 'true', BASE_URL: 'https://glance-privacy.vercel.app',
    PAYOS_CLIENT_ID: 'test-client', PAYOS_API_KEY: 'test-key', PAYOS_CHECKSUM_KEY: 'test-checksum' });
  const good = { method: 'POST', headers: { origin: 'https://glance-privacy.vercel.app', 'content-type': 'application/json' }, body: { amount: 20000, file: 'mac' } };
  let calls = 0;
  global.fetch = async (url, options) => {
    calls++;
    assert.equal(url, 'https://api-merchant.payos.vn/v2/payment-requests');
    const body = JSON.parse(options.body);
    assert.equal(body.amount, 20000);
    assert.match(body.signature, /^[a-f0-9]{64}$/);
    return { ok: true, json: async () => ({ code: '00', data: { checkoutUrl: 'https://pay.payos.vn/test' } }) };
  };
  const ok = response(); await create(good, ok);
  assert.equal(ok.code, 200); assert.equal(ok.body.checkoutUrl, 'https://pay.payos.vn/test');
  const badOrigin = response(); await create({ ...good, headers: { ...good.headers, origin: 'https://example.com' } }, badOrigin);
  assert.equal(badOrigin.code, 403);
  const badAmount = response(); await create({ ...good, body: { amount: -1 } }, badAmount);
  assert.equal(badAmount.code, 400); assert.equal(calls, 1);
});
