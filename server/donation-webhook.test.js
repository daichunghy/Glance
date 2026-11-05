const test = require('node:test');
const assert = require('node:assert/strict');
const { spawn } = require('node:child_process');
const crypto = require('node:crypto');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');
const net = require('node:net');

test('a donation webhook does not create a legacy license or order', async t => {
  const root = fs.mkdtempSync(path.join(os.tmpdir(), 'glance-webhook-test-'));
  t.after(() => fs.rmSync(root, { recursive: true, force: true }));
  const serverDir = path.join(root, 'server');
  fs.mkdirSync(serverDir);
  for (const file of ['server.js', 'donation.js']) fs.copyFileSync(path.join(__dirname, file), path.join(serverDir, file));
  const port = await new Promise((resolve, reject) => {
    const probe = net.createServer();
    probe.once('error', reject);
    probe.listen(0, '127.0.0.1', () => { const value = probe.address().port; probe.close(() => resolve(value)); });
  });
  const proc = spawn(process.execPath, [path.join(serverDir, 'server.js')], {
    env: { ...process.env, PORT: String(port), PAYOS_CLIENT_ID: 'test', PAYOS_API_KEY: 'test', PAYOS_CHECKSUM_KEY: 'test-checksum' },
    stdio: ['ignore', 'pipe', 'pipe']
  });
  t.after(() => proc.kill());
  await new Promise((resolve, reject) => {
    proc.stdout.once('data', resolve);
    proc.once('error', reject);
    proc.once('exit', code => reject(new Error(`test server exited ${code}`)));
  });
  const data = { amount: 20000, code: '00', orderCode: 42 };
  const canonical = Object.keys(data).sort().map(key => `${key}=${data[key]}`).join('&');
  const signature = crypto.createHmac('sha256', 'test-checksum').update(canonical).digest('hex');
  const response = await fetch(`http://127.0.0.1:${port}/api/payment/webhook`, {
    method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ data, signature })
  });
  assert.equal(response.status, 200);
  assert.equal(fs.existsSync(path.join(serverDir, 'licenses.json')), false);
  assert.equal(fs.existsSync(path.join(serverDir, 'orders.json')), false);
});
