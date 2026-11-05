(() => {
  const files = { mac: 'assets/product/Glance-macOS-1.0.0.zip', windows: 'assets/product/Glance-Windows.zip' };
  const params = new URLSearchParams(location.search);
  const file = Object.hasOwn(files, params.get('file')) ? params.get('file') : null;
  const manual = document.getElementById('manual-download');
  if (file) {
    manual.href = files[file];
    document.getElementById('download-notice').hidden = false;
    if (!params.has('support')) manual.click();
    else document.getElementById('download-message').textContent = 'Bạn đã chọn bản tải Glance.';
  }

  const form = document.getElementById('support-form');
  const amount = document.getElementById('support-amount');
  const status = form.querySelector('.support-status');
  const button = form.querySelector('.support-submit');
  const presets = [...form.querySelectorAll('input[name="preset"]')];
  for (const preset of presets) preset.addEventListener('change', () => { if (preset.checked) amount.value = preset.value; });
  amount.addEventListener('input', () => { for (const preset of presets) preset.checked = preset.value === amount.value; });

  fetch('/api/donation/config', { cache: 'no-store' })
    .then(response => response.ok ? response.json() : null)
    .then(config => {
      if (!config?.enabled) throw new Error();
      button.disabled = false;
      status.textContent = params.has('support') ? 'Bạn có thể kiểm tra kết quả thanh toán trên PayOS.' : '';
    }).catch(() => { status.textContent = 'Hiện chưa thể nhận ủng hộ. Bạn vẫn có thể tải Glance miễn phí.'; });

  form.addEventListener('submit', async event => {
    event.preventDefault();
    if (!form.reportValidity()) return;
    button.disabled = true;
    status.textContent = 'Đang mở PayOS…';
    try {
      const response = await fetch('/api/donation/create', {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ amount: Number(amount.value), file })
      });
      const data = await response.json();
      if (!response.ok) throw new Error();
      const checkout = new URL(data.checkoutUrl);
      if (checkout.protocol !== 'https:' || !(checkout.hostname === 'payos.vn' || checkout.hostname.endsWith('.payos.vn'))) throw new Error();
      location.assign(checkout.href);
    } catch {
      status.textContent = 'Chưa mở được PayOS. Bạn vui lòng thử lại sau.';
      button.disabled = false;
    }
  });
})();
