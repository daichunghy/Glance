(() => {
  /* ==========================================================================
     1. BUTTERY-SMOOTH APPLE PRO AMBIENT PLAY + 60FPS QUEUED SCRUB ENGINE
     ========================================================================== */
  const video = document.getElementById('scrub-video');
  if (video) {
    let isInteracting = false;
    let idleTimer = null;
    let currentPos = 0.5;
    let targetPos = 0.5;
    let isSeeking = false;
    let queuedSeekTime = null;

    video.muted = true;
    video.loop = true;
    video.playsInline = true;

    // Fast non-blocking seek with queue to eliminate decoder stutter
    function dispatchSeek(time) {
      if (isSeeking) {
        queuedSeekTime = time;
        return;
      }
      isSeeking = true;
      if ('fastSeek' in video) {
        video.fastSeek(time);
      } else {
        video.currentTime = time;
      }
    }

    video.addEventListener('seeked', () => {
      isSeeking = false;
      if (queuedSeekTime !== null && Math.abs(video.currentTime - queuedSeekTime) > 0.015) {
        const nextTime = queuedSeekTime;
        queuedSeekTime = null;
        dispatchSeek(nextTime);
      } else {
        queuedSeekTime = null;
      }
    });

    // Start ambient continuous smooth loop for optimal viewing duration
    function startAmbientPlay() {
      if (video.paused && !isInteracting) {
        video.play().catch(() => {});
      }
    }

    if (video.readyState >= 2) {
      startAmbientPlay();
    } else {
      video.addEventListener('canplay', startAmbientPlay, { once: true });
    }

    // Pointer movement handler: pause ambient loop, scrub smoothly with mouse
    function onPointerMove(clientX) {
      isInteracting = true;
      if (!video.paused) {
        video.pause();
      }
      targetPos = Math.max(0, Math.min(1, clientX / window.innerWidth));

      clearTimeout(idleTimer);
      // Auto-resume ambient playback 1.8s after cursor rests
      idleTimer = setTimeout(() => {
        isInteracting = false;
        startAmbientPlay();
      }, 1800);
    }

    window.addEventListener('mousemove', (e) => onPointerMove(e.clientX), { passive: true });
    window.addEventListener('touchmove', (e) => {
      if (e.touches.length > 0) onPointerMove(e.touches[0].clientX);
    }, { passive: true });
    window.addEventListener('touchend', () => {
      clearTimeout(idleTimer);
      idleTimer = setTimeout(() => {
        isInteracting = false;
        startAmbientPlay();
      }, 800);
    }, { passive: true });

    // 60fps spring interpolation loop when user is actively scrubbing
    function animateScrub() {
      if (isInteracting && video.readyState >= 2 && video.duration) {
        currentPos += (targetPos - currentPos) * 0.15; // Smooth responsive spring
        const desiredTime = currentPos * video.duration;
        dispatchSeek(desiredTime);
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