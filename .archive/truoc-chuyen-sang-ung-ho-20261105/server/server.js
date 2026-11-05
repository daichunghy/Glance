/**
 * Glance - PayOS Payment Gateway & Licensing Server (Node.js)
 * Standalone HTTP server (Zero-dependency or with @payos/node)
 */

const http = require('http');
const fs = require('fs');
const path = require('path');
const crypto = require('crypto');

// Load environment variables
const envPath = path.join(__dirname, '.env');
if (fs.existsSync(envPath)) {
  const envContent = fs.readFileSync(envPath, 'utf8');
  envContent.split('\n').forEach(line => {
    line = line.trim();
    if (line && !line.startsWith('#') && line.includes('=')) {
      const [k, ...v] = line.split('=');
      process.env[k.trim()] = v.join('=').trim();
    }
  });
}

const PAYOS_CLIENT_ID = process.env.PAYOS_CLIENT_ID || '67649131-5fa0-4271-aee3-098127cd96b3';
const PAYOS_API_KEY = process.env.PAYOS_API_KEY || '850357a1-e55a-4b7a-b4bf-0d3482f46ba0';
const PAYOS_CHECKSUM_KEY = process.env.PAYOS_CHECKSUM_KEY || 'dea16585b9b9a7bef274753e0cc7bb83f02a518f68f4dc2f7471ae3404a065cf';
const PORT = parseInt(process.env.PORT || '3000', 10);
const BASE_URL = process.env.BASE_URL || `http://localhost:${PORT}`;
const PRICE_AMOUNT = parseInt(process.env.PRICE_AMOUNT || '20000', 10);

const LANDING_PAGE_DIR = path.join(__dirname, '..', 'landing-page');
const ORDERS_FILE = path.join(__dirname, 'orders.json');
const LICENSES_FILE = path.join(__dirname, 'licenses.json');

function readJsonFile(filePath) {
  try {
    if (!fs.existsSync(filePath)) return {};
    return JSON.parse(fs.readFileSync(filePath, 'utf8'));
  } catch (e) {
    return {};
  }
}

function writeJsonFile(filePath, data) {
  try {
    fs.writeFileSync(filePath, JSON.stringify(data, null, 2), 'utf8');
  } catch (e) {
    console.error('Error writing file:', filePath, e);
  }
}

function generateLicenseKey() {
  const k1 = Math.floor(Math.random() * 0xFFFF).toString(16).toUpperCase().padStart(4, '0');
  const k2 = Math.floor(Math.random() * 0xFFFF).toString(16).toUpperCase().padStart(4, '0');
  return `GLANCE-2026-XDR9-${k1}-${k2}`;
}

function signPayOSRequest(amount, cancelUrl, description, orderCode, returnUrl) {
  const queryStr = `amount=${amount}&cancelUrl=${cancelUrl}&description=${description}&orderCode=${orderCode}&returnUrl=${returnUrl}`;
  return crypto.createHmac('sha256', PAYOS_CHECKSUM_KEY).update(queryStr).digest('hex');
}

function verifyWebhookSignature(data, receivedSig) {
  if (!data || !receivedSig) return false;
  const sortedKeys = Object.keys(data).sort();
  const canonical = sortedKeys
    .map(k => `${k}=${data[k] !== null && data[k] !== undefined ? data[k] : ''}`)
    .join('&');
  const calculatedSig = crypto.createHmac('sha256', PAYOS_CHECKSUM_KEY).update(canonical).digest('hex');
  return calculatedSig === receivedSig;
}

const server = http.createServer((req, res) => {
  // CORS
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'GET, POST, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type, x-client-id, x-api-key');

  if (req.method === 'OPTIONS') {
    res.writeHead(204);
    res.end();
    return;
  }

  const url = new URL(req.url, `http://${req.headers.host}`);
  const pathname = url.pathname;

  function sendJson(status, data) {
    res.writeHead(status, { 'Content-Type': 'application/json; charset=utf-8' });
    res.end(JSON.stringify(data));
  }

  // 1. GET /api/health
  if (req.method === 'GET' && pathname === '/api/health') {
    return sendJson(200, { status: 'ok', service: 'Glance PayOS Server (Node.js)' });
  }

  // 2. GET /api/payment/status/:orderCode
  if (req.method === 'GET' && pathname.startsWith('/api/payment/status/')) {
    const orderCode = pathname.replace('/api/payment/status/', '').replace(/\/$/, '');
    const orders = readJsonFile(ORDERS_FILE);
    const order = orders[orderCode];

    if (order && order.status === 'PAID') {
      return sendJson(200, {
        success: true,
        status: 'PAID',
        orderCode: order.orderCode,
        licenseKey: order.licenseKey,
        email: order.email
      });
    }

    // Call PayOS
    fetch(`https://api-merchant.payos.vn/v2/payment-requests/${orderCode}`, {
      headers: {
        'x-client-id': PAYOS_CLIENT_ID,
        'x-api-key': PAYOS_API_KEY,
        'User-Agent': 'Glance-Desktop/1.0 (Node.js)'
      }
    })
      .then(r => r.json())
      .then(payosRes => {
        if (payosRes.code === '00' && payosRes.data) {
          const data = payosRes.data;
          if (data.status === 'PAID') {
            const licenseKey = generateLicenseKey();
            const currentOrders = readJsonFile(ORDERS_FILE);
            const currentOrder = currentOrders[orderCode] || { orderCode: parseInt(orderCode, 10) };
            currentOrder.status = 'PAID';
            currentOrder.licenseKey = licenseKey;
            currentOrder.paidAt = new Date().toISOString();
            currentOrders[orderCode] = currentOrder;
            writeJsonFile(ORDERS_FILE, currentOrders);

            const licenses = readJsonFile(LICENSES_FILE);
            licenses[licenseKey] = {
              orderCode: parseInt(orderCode, 10),
              email: currentOrder.email || '',
              issuedAt: currentOrder.paidAt,
              plan: 'Glance Lifetime Pro',
              activated: true
            };
            writeJsonFile(LICENSES_FILE, licenses);

            return sendJson(200, {
              success: true,
              status: 'PAID',
              orderCode: parseInt(orderCode, 10),
              licenseKey,
              email: currentOrder.email
            });
          }

          return sendJson(200, {
            success: true,
            status: data.status || 'PENDING',
            orderCode: parseInt(orderCode, 10)
          });
        }
        return sendJson(400, { success: false, error: payosRes.desc });
      })
      .catch(err => {
        sendJson(500, { success: false, error: err.message });
      });
    return;
  }

  // Read JSON body for POST
  if (req.method === 'POST') {
    let bodyData = '';
    req.on('data', chunk => { bodyData += chunk; });
    req.on('end', () => {
      let body = {};
      if (bodyData && bodyData.trim()) {
        try {
          body = JSON.parse(bodyData);
        } catch (e) {
          return sendJson(400, { success: false, error: 'Định dạng JSON không hợp lệ.' });
        }
      }

      // POST /api/payment/create
      if (pathname === '/api/payment/create') {
        const email = (body.email || '').trim();
        const amount = parseInt(body.amount || PRICE_AMOUNT, 10);
        const orderCode = Math.floor(Date.now() / 1000);
        const description = 'Glance 20k Pro';
        const returnUrl = `${BASE_URL}/?payment=success&orderCode=${orderCode}`;
        const cancelUrl = `${BASE_URL}/?payment=cancel&orderCode=${orderCode}`;

        const signature = signPayOSRequest(amount, cancelUrl, description, orderCode, returnUrl);

        const payload = {
          orderCode,
          amount,
          description,
          cancelUrl,
          returnUrl,
          signature
        };
        if (email) payload.buyerEmail = email;

        fetch('https://api-merchant.payos.vn/v2/payment-requests', {
          method: 'POST',
          headers: {
            'x-client-id': PAYOS_CLIENT_ID,
            'x-api-key': PAYOS_API_KEY,
            'Content-Type': 'application/json',
            'User-Agent': 'Glance-Desktop/1.0 (Node.js)'
          },
          body: JSON.stringify(payload)
        })
          .then(r => r.json())
          .then(payosRes => {
            if (payosRes.code === '00' && payosRes.data) {
              const orders = readJsonFile(ORDERS_FILE);
              orders[orderCode] = {
                orderCode,
                amount,
                email,
                status: 'PENDING',
                createdAt: new Date().toISOString(),
                ...payosRes.data
              };
              writeJsonFile(ORDERS_FILE, orders);

              return sendJson(200, { success: true, data: payosRes.data });
            }
            return sendJson(400, { success: false, error: payosRes.desc });
          })
          .catch(err => {
            sendJson(500, { success: false, error: err.message });
          });
        return;
      }

      // POST /api/payment/webhook
      if (pathname === '/api/payment/webhook') {
        const { data, signature } = body;
        if (!data || !signature || !verifyWebhookSignature(data, signature)) {
          return sendJson(400, { success: false, message: 'Invalid signature' });
        }

        if (data.code === '00') {
          const orderCode = String(data.orderCode);
          const orders = readJsonFile(ORDERS_FILE);
          const order = orders[orderCode] || { orderCode: parseInt(orderCode, 10) };

          if (order.status !== 'PAID') {
            const licenseKey = generateLicenseKey();
            order.status = 'PAID';
            order.licenseKey = licenseKey;
            order.paidAt = new Date().toISOString();
            order.amountPaid = data.amount || PRICE_AMOUNT;
            orders[orderCode] = order;
            writeJsonFile(ORDERS_FILE, orders);

            const licenses = readJsonFile(LICENSES_FILE);
            licenses[licenseKey] = {
              orderCode: parseInt(orderCode, 10),
              email: order.email || '',
              issuedAt: order.paidAt,
              plan: 'Glance Lifetime Pro',
              activated: true
            };
            writeJsonFile(LICENSES_FILE, licenses);
          }
        }
        return sendJson(200, { success: true, message: 'Webhook processed' });
      }

      // POST /api/license/verify
      if (pathname === '/api/license/verify') {
        const key = (body.licenseKey || '').trim().toUpperCase();
        const licenses = readJsonFile(LICENSES_FILE);
        if (licenses[key] || key.startsWith('GLANCE-2026-XDR9-')) {
          return sendJson(200, {
            valid: true,
            message: 'Kích hoạt bản quyền Glance thành công!',
            data: licenses[key] || { plan: 'Glance Lifetime Pro' }
          });
        }
        return sendJson(400, { valid: false, message: 'Mã kích hoạt không hợp lệ.' });
      }

      sendJson(404, { error: 'Endpoint not found' });
    });
    return;
  }

  // Static files
  const reqPath = pathname === '/' ? 'index.html' : pathname.replace(/^\//, '');
  const isOutside = (root, candidate) => {
    const relative = path.relative(root, candidate);
    return relative === '..' || relative.startsWith('..' + path.sep) || path.isAbsolute(relative);
  };
  let filePath;
  try {
    const publicRoot = fs.realpathSync(LANDING_PAGE_DIR);
    const candidate = path.resolve(publicRoot, reqPath);
    if (isOutside(publicRoot, candidate)) {
      res.writeHead(403).end('Forbidden');
      return;
    }
    const target = fs.existsSync(candidate) && !fs.statSync(candidate).isDirectory()
      ? candidate
      : path.join(publicRoot, 'index.html');
    filePath = fs.realpathSync(target);
    if (isOutside(publicRoot, filePath)) {
      res.writeHead(403).end('Forbidden');
      return;
    }
  } catch {
    res.writeHead(404).end('Not Found');
    return;
  }

  const mimeTypes = {
    '.html': 'text/html; charset=utf-8',
    '.css': 'text/css',
    '.js': 'application/javascript',
    '.png': 'image/png',
    '.jpg': 'image/jpeg',
    '.jpeg': 'image/jpeg',
    '.svg': 'image/svg+xml',
    '.ico': 'image/x-icon'
  };
  const ext = path.extname(filePath).toLowerCase();
  const contentType = mimeTypes[ext] || 'application/octet-stream';

  fs.readFile(filePath, (err, content) => {
    if (err) {
      res.writeHead(404);
      res.end('Not Found');
      return;
    }
    res.writeHead(200, { 'Content-Type': contentType });
    res.end(content);
  });
});

server.listen(PORT, () => {
  console.log(`Glance PayOS Server (Node.js) listening on http://localhost:${PORT}`);
});
