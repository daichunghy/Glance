(() => {
  /* ==========================================================================
     1. BUTTERY-SMOOTH APPLE PRO MOUSE-SCRUB ENGINE (Lerp + RAF)
     ========================================================================== */
  const video = document.getElementById('scrub-video');
  if (video) {
    let currentPos = 0.35;
    let targetPos = 0.35;

    video.addEventListener('loadedmetadata', () => {
      video.currentTime = video.duration * 0.35;
    });

    // Update targetPos based on normalized mouse horizontal position
    window.addEventListener('mousemove', (e) => {
      targetPos = Math.max(0, Math.min(1, e.clientX / window.innerWidth));
    });

    // Mobile touch scrubbing
    window.addEventListener('touchmove', (e) => {
      if (e.touches.length > 0) {
        targetPos = Math.max(0, Math.min(1, e.touches[0].clientX / window.innerWidth));
      }
    }, { passive: true });

    // Physics-based smooth rendering loop
    function animateScrub() {
      if (video.readyState >= 2 && video.duration) {
        currentPos += (targetPos - currentPos) * 0.085; // Smooth spring interpolation
        const desiredTime = currentPos * video.duration;
        if (!video.seeking && Math.abs(video.currentTime - desiredTime) > 0.02) {
          video.currentTime = desiredTime;
        }
      }
      requestAnimationFrame(animateScrub);
    }
    requestAnimationFrame(animateScrub);
  }

  /* ==========================================================================
     2. DOWNLOADS & PAYOS DONATION LOGIC
     ========================================================================== */
  const files = {
    mac: 'assets/product/Glance-macOS-1.0.0.zip',
    windows: 'assets/product/Glance-Windows.zip'
  };
  const params = new URLSearchParams(location.search);
  const file = Object.hasOwn(files, params.get('file')) ? params.get('file') : null;
  const manual = document.getElementById('manual-download');

  if (file && manual) {
    manual.href = files[file];
    const notice = document.getElementById('download-notice');
    if (notice) notice.hidden = false;
    if (!params.has('support')) {
      manual.click();
    } else {
      const msg = document.getElementById('download-message');
      if (msg) msg.textContent = 'Bạn đã chọn bản cài đặt Glance.';
    }
  }

  const form = document.getElementById('support-form');
  if (!form) return;

  const amount = document.getElementById('support-amount');
  const status = document.getElementById('support-status');
  const button = document.getElementById('submit-btn');
  const btnText = button.querySelector('.btn-text');
  const noteBox = document.getElementById('preset-note');
  const presets = [...form.querySelectorAll('input[name="preset"]')];
  const pillLabels = [...form.querySelectorAll('.apple-pill')];

  // Preset switching
  presets.forEach((preset, idx) => {
    preset.addEventListener('change', () => {
      if (preset.checked) {
        amount.value = preset.value;
        pillLabels.forEach(p => p.classList.remove('is-selected'));
        pillLabels[idx]?.classList.add('is-selected');

        const note = preset.dataset.note;
        if (note && noteBox) noteBox.textContent = note;
      }
    });
  });

  // Custom amount syncing
  amount.addEventListener('input', () => {
    let matched = false;
    presets.forEach((preset, idx) => {
      if (preset.value === amount.value) {
        preset.checked = true;
        pillLabels.forEach(p => p.classList.remove('is-selected'));
        pillLabels[idx]?.classList.add('is-selected');
        matched = true;
        if (noteBox && preset.dataset.note) noteBox.textContent = preset.dataset.note;
      } else {
        preset.checked = false;
      }
    });
    if (!matched) {
      pillLabels.forEach(p => p.classList.remove('is-selected'));
      if (noteBox) {
        noteBox.textContent = 'Nếu app hay và thú vị bạn có thể ủng hộ mình để tiếp tục phát triển nha ☕💙';
      }
    }
  });

  // Status message from PayOS return
  if (params.get('support') === 'return') {
    status.style.color = '#2ed573';
    status.textContent = 'Cảm ơn tấm lòng của bạn! Món quà tiếp sức đã được ghi nhận. 💙';
  } else if (params.get('support') === 'cancel') {
    status.style.color = '#b5b6bc';
    status.textContent = 'Bạn đã hủy lượt tiếp sức. Chúc bạn có trải nghiệm tuyệt vời với Glance!';
  }

  // Pre-fetch config quietly in background without blocking
  let isConfigured = null;
  fetch('/api/donation/config', { cache: 'no-store' })
    .then(res => res.ok ? res.json() : null)
    .then(cfg => { isConfigured = Boolean(cfg?.enabled); })
    .catch(() => { isConfigured = false; });

  // Handle PayOS submit
  form.addEventListener('submit', async event => {
    event.preventDefault();
    if (!form.reportValidity()) return;

    button.disabled = true;
    if (btnText) btnText.textContent = 'Đang mở cổng PayOS…';
    status.textContent = '';

    try {
      if (isConfigured === false) {
        throw new Error('CONFIG_DISABLED');
      }

      const response = await fetch('/api/donation/create', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ amount: Number(amount.value), file })
      });

      const data = await response.json();
      if (!response.ok) throw new Error(data.error || 'CREATE_FAILED');

      const checkout = new URL(data.checkoutUrl);
      if (checkout.protocol !== 'https:' || !(checkout.hostname === 'payos.vn' || checkout.hostname.endsWith('.payos.vn'))) {
        throw new Error('INVALID_CHECKOUT_URL');
      }

      location.assign(checkout.href);
    } catch (err) {
      if (err.message === 'CONFIG_DISABLED') {
        status.style.color = '#ff9f43';
        status.textContent = 'Cổng tiếp sức đang được cập nhật. Bạn vẫn có thể trải nghiệm Glance hoàn toàn miễn phí!';
      } else {
        status.style.color = '#ff6b6b';
        status.textContent = 'Chưa thể kết nối PayOS lúc này. Bạn vui lòng thử lại sau giây lát nhé!';
      }
      button.disabled = false;
      if (btnText) btnText.textContent = 'Ủng hộ qua PayOS ☕';
    }
  });
})();