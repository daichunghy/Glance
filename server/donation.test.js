const test = require('node:test');
const assert = require('node:assert/strict');
const { createDonation } = require('./donation');

const config = { clientId: 'test-client', apiKey: 'test-key', checksumKey: 'test-checksum', baseUrl: 'https://glance.example' };

test('creates a one-time support link for the selected amount', async () => {
  let request;
  const fetcher = async (url, options) => {
    request = { url, options, body: JSON.parse(options.body) };
    return { ok: true, json: async () => ({ code: '00', data: { checkoutUrl: 'https://pay.payos.vn/test' } }) };
  };
  const result = await createDonation({ amount: 20000, file: 'mac', config, fetcher, orderCode: 12345 });
  assert.equal(result.checkoutUrl, 'https://pay.payos.vn/test');
  assert.equal(request.body.amount, 20000);
  assert.equal(request.body.orderCode, 12345);
  assert.equal(request.body.description, 'Ung ho');
  assert.equal(request.body.returnUrl, 'https://glance.example/ung-ho.html?file=mac&support=return');
  assert.ok(request.body.signature);
  assert.equal(request.body.buyerEmail, undefined);
});

test('rejects invalid amounts without contacting the gateway', async () => {
  for (const amount of [0, -10, 10.5, '20000', 100000001]) {
    await assert.rejects(createDonation({ amount, config, fetcher: () => { throw Error('unexpected network'); } }), /số tiền/i);
  }
});

test('does not accept an untrusted checkout link or missing configuration', async () => {
  await assert.rejects(createDonation({ amount: 20000, config: {}, fetcher: () => {} }), /cấu hình/i);
  const fetcher = async () => ({ ok: true, json: async () => ({ code: '00', data: { checkoutUrl: 'https://payos.vn.example.com/x' } }) });
  await assert.rejects(createDonation({ amount: 20000, config, fetcher }), /thanh toán/i);
});
