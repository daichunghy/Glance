'use strict';

const crypto = require('node:crypto');

async function createDonation({ amount, file, config, fetcher = fetch, orderCode = crypto.randomInt(1, 2147483647) }) {
  if (!Number.isSafeInteger(amount) || amount < 1000 || amount > 100000000) {
    throw new Error('Số tiền ủng hộ không hợp lệ.');
  }
  if (!config?.clientId || !config?.apiKey || !config?.checksumKey || !config?.baseUrl) {
    throw new Error('Chưa có cấu hình nhận ủng hộ.');
  }
  const base = new URL(config.baseUrl);
  if (base.protocol !== 'https:' && base.hostname !== 'localhost' && base.hostname !== '127.0.0.1') {
    throw new Error('Cấu hình địa chỉ nhận ủng hộ không hợp lệ.');
  }
  const target = file === 'mac' || file === 'windows' ? `file=${file}&` : '';
  const returnUrl = new URL(`/ung-ho.html?${target}support=return`, base).href;
  const cancelUrl = new URL(`/ung-ho.html?${target}support=cancel`, base).href;
  const description = 'Ung ho';
  const signature = crypto.createHmac('sha256', config.checksumKey)
    .update(`amount=${amount}&cancelUrl=${cancelUrl}&description=${description}&orderCode=${orderCode}&returnUrl=${returnUrl}`)
    .digest('hex');
  const response = await fetcher('https://api-merchant.payos.vn/v2/payment-requests', {
    method: 'POST',
    headers: { 'x-client-id': config.clientId, 'x-api-key': config.apiKey, 'Content-Type': 'application/json' },
    body: JSON.stringify({ amount, orderCode, description, returnUrl, cancelUrl, signature })
  });
  const payload = await response.json();
  if (!response.ok || payload.code !== '00') throw new Error('Không thể tạo liên kết thanh toán.');
  let checkout;
  try { checkout = new URL(payload.data?.checkoutUrl); } catch { throw new Error('Liên kết thanh toán không hợp lệ.'); }
  if (checkout.protocol !== 'https:' || !(checkout.hostname === 'payos.vn' || checkout.hostname.endsWith('.payos.vn'))) {
    throw new Error('Liên kết thanh toán không hợp lệ.');
  }
  return { checkoutUrl: checkout.href };
}

module.exports = { createDonation };
