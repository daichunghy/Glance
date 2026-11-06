(() => {
  /* ==========================================================================
     1. BACKGROUND VIDEO MOUSE-SCRUBBING ENGINE
     ========================================================================== */
  const video = document.getElementById('scrub-video');
  if (video) {
    let prevX = null;
    let targetTime = 0;
    let isSeeking = false;
    const SENSITIVITY = 0.85;

    // Wait until video metadata is loaded to calculate duration accurately
    video.addEventListener('loadedmetadata', () => {
      targetTime = video.duration * 0.35;
      video.currentTime = targetTime;
    });

    // Horizontal mouse scrubbing
    window.addEventListener('mousemove', (e) => {
      if (prevX === null) {
        prevX = e.clientX;
        return;
      }
      const delta = e.clientX - prevX;
      prevX = e.clientX;

      if (!video.duration) return;

      const timeOffset = (delta / window.innerWidth) * SENSITIVITY * video.duration;
      targetTime = Math.max(0, Math.min(video.duration, targetTime + timeOffset));

      if (!isSeeking) {
        isSeeking = true;
        video.currentTime = targetTime;
      }
    });

    // Seeked queueing to prevent seek-flooding
    video.addEventListener('seeked', () => {
      if (Math.abs(video.currentTime - targetTime) > 0.04) {
        video.currentTime = targetTime;
      } else {
        isSeeking = false;
      }
    });

    // Touch support for mobile scrubbing
    let touchStartX = null;
    window.addEventListener('touchstart', (e) => {
      if (e.touches.length > 0) touchStartX = e.touches[0].clientX;
    }, { passive: true });

    window.addEventListener('touchmove', (e) => {
      if (touchStartX === null || !video.duration || e.touches.length === 0) return;
      const currentX = e.touches[0].clientX;
      const delta = currentX - touchStartX;
      touchStartX = currentX;

      const timeOffset = (delta / window.innerWidth) * SENSITIVITY * video.duration;
      targetTime = Math.max(0, Math.min(video.duration, targetTime + timeOffset));

      if (!isSeeking) {
        isSeeking = true;
        video.currentTime = targetTime;
      }
    }, { passive: true });
  }

  /* ==========================================================================
     2. TYPEWRITER EFFECT WITH BLINKING CURSOR
     ========================================================================== */
  const typewriterEl = document.getElementById('typewriter-text');
  if (typewriterEl) {
    const fullText = "Glance hoàn toàn miễn phí. Nếu app hay và thú vị, bạn có thể ủng hộ mình để tiếp tục phát triển nha ☕💙";
    const speed = 32;
    const startDelay = 500;

    setTimeout(() => {
      let index = 0;
      typewriterEl.textContent = '';

      const cursor = document.createElement('span');
      cursor.className = 'blinking-cursor';
      typewriterEl.after(cursor);

      const interval = setInterval(() => {
        if (index < fullText.length) {
          typewriterEl.textContent += fullText.charAt(index);
          index++;
        } else {
          clearInterval(interval);
          setTimeout(() => cursor.remove(), 2500); // Remove cursor after done
        }
      }, speed);
    }, startDelay);
  }

  /* ==========================================================================
     3. DOWNLOAD & PAYOS INTERACTION LOGIC
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
  const pillLabels = [...form.querySelectorAll('.pill-btn')];

  // Update note & custom input when clicking presets
  presets.forEach((preset, idx) => {
    preset.addEventListener('change', () => {
      if (preset.checked) {
        amount.value = preset.value;
        pillLabels.forEach(p => p.classList.remove('is-active'));
        pillLabels[idx]?.classList.add('is-active');

        const note = preset.dataset.note;
        if (note && noteBox) noteBox.textContent = note;
      }
    });
  });

  // When user types custom amount, sync preset pills
  amount.addEventListener('input', () => {
    let matched = false;
    presets.forEach((preset, idx) => {
      if (preset.value === amount.value) {
        preset.checked = true;
        pillLabels.forEach(p => p.classList.remove('is-active'));
        pillLabels[idx]?.classList.add('is-active');
        matched = true;
        if (noteBox && preset.dataset.note) noteBox.textContent = preset.dataset.note;
      } else {
        preset.checked = false;
      }
    });
    if (!matched) {
      pillLabels.forEach(p => p.classList.remove('is-active'));
      if (noteBox) {
        noteBox.textContent = 'Mọi sự tiếp sức từ bạn đều là nguồn động viên vô giá đối với Glance. Cảm ơn bạn rất nhiều! 💙';
      }
    }
  });

  // Handle return or cancel status from PayOS
  if (params.get('support') === 'return') {
    status.style.color = '#2ed573';
    status.textContent = 'Cảm ơn tấm lòng của bạn! Món quà tiếp sức đã được ghi nhận. 💙';
  } else if (params.get('support') === 'cancel') {
    status.style.color = '#b5b6bc';
    status.textContent = 'Bạn đã hủy lượt tiếp sức. Chúc bạn có trải nghiệm tuyệt vời với Glance!';
  }

  // Pre-fetch config quietly in background without disabling UI or blocking user!
  let isConfigured = null;
  fetch('/api/donation/config', { cache: 'no-store' })
    .then(res => res.ok ? res.json() : null)
    .then(cfg => { isConfigured = Boolean(cfg?.enabled); })
    .catch(() => { isConfigured = false; });

  // Handle form submission
  form.addEventListener('submit', async event => {
    event.preventDefault();
    if (!form.reportValidity()) return;

    button.disabled = true;
    if (btnText) btnText.textContent = 'Đang chuyển đến PayOS…';
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