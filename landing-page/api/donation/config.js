'use strict';

function configured() {
  if (process.env.GLANCE_DONATIONS_ENABLED !== 'true' || !process.env.PAYOS_CLIENT_ID ||
      !process.env.PAYOS_API_KEY || !process.env.PAYOS_CHECKSUM_KEY) return false;
  try {
    const base = new URL(process.env.BASE_URL);
    return base.protocol === 'https:' && base.origin === 'https://glance-privacy.vercel.app';
  } catch { return false; }
}

module.exports = function handler(req, res) {
  res.setHeader('Cache-Control', 'no-store');
  if (req.method !== 'GET') return res.status(405).json({ error: 'Phương thức không được hỗ trợ.' });
  return res.status(200).json({ enabled: configured() });
};
module.exports.configured = configured;
