(() => {
  const $ = id => document.getElementById(id);
  const dialog = $('checkout');
  const form = $('checkout-form');
  const status = $('payment-status');
  const orderBox = $('checkout-order');
  const qr = $('checkout-qr');
  const payLink = $('payos-link');
  const result = $('license-result');
  const key = $('license-key');
  const create = $('create-order');
  const check = $('check-order');
  let orderCode, pending = false, completed = false, creating = false, timer, started;

  function schedule() {
    clearTimeout(timer);
    if (!pending || !dialog.open) return;
    if (Date.now() - started > 600000) {
      status.textContent = 'Nếu bạn đã thanh toán, hãy bấm Kiểm tra thanh toán.';
      return;
    }
    timer = setTimeout(poll, 2800);
  }

  async function poll(manual = false) {
    if (!orderCode || completed || check.disabled) return;
    clearTimeout(timer);
    check.disabled = true;
    if (manual) status.textContent = 'Đang kiểm tra thanh toán…';
    try {
      const response = await fetch(`/api/payment/status/${encodeURIComponent(orderCode)}`, { cache: 'no-store' });
      if (!response.ok) throw new Error();
      const data = await response.json();
      if (data.status === 'PAID' && typeof data.licenseKey === 'string' && data.licenseKey.trim()) {
        completed = true;
        pending = false;
        orderBox.hidden = true;
        key.textContent = data.licenseKey;
        result.hidden = false;
        status.textContent = 'PayOS đã xác nhận thanh toán. Hãy sao chép mã và nhập vào Glance.';
      } else if (['CANCELLED', 'EXPIRED'].includes(data.status)) {
        pending = false;
        orderCode = undefined;
        orderBox.hidden = true;
        form.hidden = false;
        status.textContent = 'Đơn này đã đóng. Bạn có thể tạo một đơn mới.';
      } else if (manual) {
        status.textContent = 'PayOS chưa xác nhận khoản thanh toán. Bạn có thể kiểm tra lại sau.';
      }
    } catch {
      if (manual) status.textContent = 'Trang chưa kiểm tra được giao dịch. Bạn hãy thử lại sau.';
    } finally {
      check.disabled = false;
      schedule();
    }
  }

  function showOrder(data) {
    const { bin, accountNumber, accountName, description, checkoutUrl } = data;
    if (typeof checkoutUrl === 'string') {
      const url = new URL(checkoutUrl);
      if (url.protocol === 'https:' && url.hostname.endsWith('.payos.vn')) {
        payLink.href = url.href;
        payLink.hidden = false;
      }
    }
    if (/^\d{6}$/.test(String(bin)) && /^[A-Z0-9]+$/i.test(String(accountNumber))) {
      const query = new URLSearchParams({ amount: '20000', addInfo: description || '', accountName: accountName || '' });
      qr.src = `https://img.vietqr.io/image/${bin}-${accountNumber}-compact2.png?${query}`;
      qr.hidden = false;
    }
    form.hidden = true;
    orderBox.hidden = false;
    status.textContent = 'Bạn có thể quét VietQR hoặc mở PayOS để thanh toán 20.000đ. Trang sẽ hiện mã kích hoạt sau khi PayOS xác nhận.';
  }

  form.addEventListener('submit', async event => {
    event.preventDefault();
    if (creating || orderCode) return;
    creating = create.disabled = true;
    status.textContent = 'Đang tạo đơn…';
    try {
      const response = await fetch('/api/payment/create', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ amount: 20000, email: $('buyer-email').value.trim() })
      });
      if (!response.ok) throw new Error();
      const payload = await response.json();
      if (!payload.success || !/^\d+$/.test(String(payload.data?.orderCode))) throw new Error();
      showOrder(payload.data);
      orderCode = payload.data.orderCode;
      pending = true;
      started = Date.now();
      schedule();
    } catch {
      status.textContent = 'Trang chưa kết nối được với PayOS. Bạn hãy thử lại sau.';
    } finally {
      creating = create.disabled = false;
    }
  });

  document.querySelectorAll('[data-checkout]').forEach(button => button.addEventListener('click', () => {
    dialog.showModal();
    if (pending) poll();
  }));
  check.addEventListener('click', () => poll(true));
  dialog.addEventListener('close', () => clearTimeout(timer));
  dialog.addEventListener('click', event => { if (event.target === dialog) {
    const r = dialog.getBoundingClientRect();
    if (event.clientX < r.left || event.clientX > r.right || event.clientY < r.top || event.clientY > r.bottom) dialog.close();
  } });
  $('copy-license').addEventListener('click', async () => {
    try {
      await navigator.clipboard.writeText(key.textContent);
      status.textContent = 'Đã sao chép mã kích hoạt.';
    } catch {
      status.textContent = 'Bạn có thể chọn mã rồi sao chép thủ công.';
    }
  });

  const query = new URLSearchParams(location.search);
  const redirectOrder = query.get('orderCode');
  if (['success', 'PAID'].includes(query.get('payment') || query.get('status')) && /^\d{1,16}$/.test(redirectOrder || '')) {
    orderCode = redirectOrder;
    pending = true;
    started = Date.now();
    form.hidden = true;
    orderBox.hidden = false;
    dialog.showModal();
    poll(true);
  }
})();
