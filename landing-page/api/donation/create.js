'use strict';

const { createDonation } = require('../../lib/donation');
const { configured } = require('./config');

module.exports = async function handler(req, res) {
  res.setHeader('Cache-Control', 'no-store');
  if (req.method !== 'POST') return res.status(405).json({ error: 'Phương thức không được hỗ trợ.' });
  if (!configured()) return res.status(503).json({ error: 'Chưa thể nhận ủng hộ.' });
  if (req.headers.origin !== new URL(process.env.BASE_URL).origin ||
      !(req.headers['content-type'] || '').toLowerCase().startsWith('application/json')) {
    return res.status(403).json({ error: 'Yêu cầu không hợp lệ.' });
  }
  const body = req.body;
  if (!body || typeof body !== 'object' || !Number.isSafeInteger(body.amount) ||
      body.amount < 1000 || body.amount > 100000000 ||
      (body.file != null && !['mac', 'windows'].includes(body.file))) {
    return res.status(400).json({ error: 'Thông tin ủng hộ không hợp lệ.' });
  }
  try {
    const result = await createDonation({ amount: body.amount, file: body.file, config: {
      clientId: process.env.PAYOS_CLIENT_ID,
      apiKey: process.env.PAYOS_API_KEY,
      checksumKey: process.env.PAYOS_CHECKSUM_KEY,
      baseUrl: process.env.BASE_URL
    }});
    return res.status(200).json(result);
  } catch {
    return res.status(502).json({ error: 'Chưa thể tạo liên kết thanh toán.' });
  }
};
