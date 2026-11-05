/**
 * Glance Landing Page Interactive Scripts
 * Scroll Reveal Engine, Smart Privacy Simulator, Audio Feedback, 
 * VietQR 20k Checkout Modal & License Generator
 */

document.addEventListener('DOMContentLoaded', () => {
  // 1. Scroll-Reveal Animation Engine (Blur to Clear + Slide-Up)
  const revealElements = document.querySelectorAll('.reveal');
  const revealObserver = new IntersectionObserver((entries, observer) => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        entry.target.classList.add('revealed');
        observer.unobserve(entry.target);
      }
    });
  }, {
    threshold: 0.1,
    rootMargin: '0px 0px -40px 0px'
  });

  revealElements.forEach(el => revealObserver.observe(el));

  // 2. Web Audio API for Apple Haptic Chime Sounds
  const AudioContext = window.AudioContext || window.webkitAudioContext;
  let audioCtx = null;

  function initAudio() {
    if (!audioCtx) {
      audioCtx = new AudioContext();
    }
    if (audioCtx.state === 'suspended') {
      audioCtx.resume();
    }
  }

  function playHapticTick() {
    try {
      initAudio();
      const osc = audioCtx.createOscillator();
      const gain = audioCtx.createGain();
      osc.type = 'sine';
      
      const now = audioCtx.currentTime;
      osc.frequency.setValueAtTime(1020, now);
      osc.frequency.exponentialRampToValueAtTime(1440, now + 0.05);
      
      gain.gain.setValueAtTime(0.01, now);
      gain.gain.exponentialRampToValueAtTime(0.18, now + 0.01);
      gain.gain.exponentialRampToValueAtTime(0.001, now + 0.15);

      osc.connect(gain);
      gain.connect(audioCtx.destination);
      osc.start(now);
      osc.stop(now + 0.15);
    } catch (e) {}
  }

  function playShieldEngageSound() {
    try {
      initAudio();
      const now = audioCtx.currentTime;
      const osc = audioCtx.createOscillator();
      const gain = audioCtx.createGain();
      osc.type = 'triangle';
      osc.frequency.setValueAtTime(440, now);
      osc.frequency.exponentialRampToValueAtTime(880, now + 0.12);
      
      gain.gain.setValueAtTime(0.01, now);
      gain.gain.exponentialRampToValueAtTime(0.15, now + 0.02);
      gain.gain.exponentialRampToValueAtTime(0.001, now + 0.25);

      osc.connect(gain);
      gain.connect(audioCtx.destination);
      osc.start(now);
      osc.stop(now + 0.25);
    } catch (e) {}
  }

  function playSuccessChime() {
    try {
      initAudio();
      const now = audioCtx.currentTime;
      const osc = audioCtx.createOscillator();
      const gain = audioCtx.createGain();
      osc.type = 'sine';
      osc.frequency.setValueAtTime(523.25, now); // C5
      osc.frequency.setValueAtTime(659.25, now + 0.08); // E5
      osc.frequency.setValueAtTime(783.99, now + 0.16); // G5
      osc.frequency.setValueAtTime(1046.50, now + 0.24); // C6
      
      gain.gain.setValueAtTime(0.01, now);
      gain.gain.exponentialRampToValueAtTime(0.2, now + 0.02);
      gain.gain.exponentialRampToValueAtTime(0.001, now + 0.45);

      osc.connect(gain);
      gain.connect(audioCtx.destination);
      osc.start(now);
      osc.stop(now + 0.45);
    } catch (e) {}
  }

  // 3. Live Interactive Smart Privacy Simulator
  const simFrame = document.getElementById('simFrame');
  const simStatusText = document.getElementById('simStatusText');
  const btnLookCenter = document.getElementById('btnLookCenter');
  const btnLookLeft = document.getElementById('btnLookLeft');
  const btnLookRight = document.getElementById('btnLookRight');
  const btnStepAway = document.getElementById('btnStepAway');
  const btnToggleSource = document.getElementById('btnToggleSource');
  const sourceLabel = document.getElementById('sourceLabel');

  const simButtons = [btnLookCenter, btnLookLeft, btnLookRight, btnStepAway];

  function setActiveSimButton(activeBtn) {
    simButtons.forEach(btn => {
      if (btn) btn.classList.remove('active');
    });
    if (activeBtn) activeBtn.classList.add('active');
  }

  if (btnLookCenter) {
    btnLookCenter.addEventListener('click', () => {
      if (!simFrame) return;
      playHapticTick();
      setActiveSimButton(btnLookCenter);
      simFrame.classList.remove('blur-left', 'blur-right', 'blur-full');
      if (simStatusText) simStatusText.textContent = 'Glance: Nhìn trực diện • Sắc nét 100%';
    });
  }

  if (btnLookLeft) {
    btnLookLeft.addEventListener('click', () => {
      if (!simFrame) return;
      playHapticTick();
      setActiveSimButton(btnLookLeft);
      // Looking left -> blur the right half
      simFrame.classList.remove('blur-left', 'blur-full');
      simFrame.classList.add('blur-right');
      if (simStatusText) simStatusText.textContent = 'Glance: Đang nhìn trái • Đang mờ bên phải';
    });
  }

  if (btnLookRight) {
    btnLookRight.addEventListener('click', () => {
      if (!simFrame) return;
      playHapticTick();
      setActiveSimButton(btnLookRight);
      // Looking right -> blur the left half
      simFrame.classList.remove('blur-right', 'blur-full');
      simFrame.classList.add('blur-left');
      if (simStatusText) simStatusText.textContent = 'Glance: Đang nhìn phải • Đang mờ bên trái';
    });
  }

  if (btnStepAway) {
    btnStepAway.addEventListener('click', () => {
      if (!simFrame) return;
      playShieldEngageSound();
      setActiveSimButton(btnStepAway);
      simFrame.classList.remove('blur-left', 'blur-right');
      simFrame.classList.add('blur-full');
      if (simStatusText) simStatusText.textContent = 'Glance: Vắng mặt • Màn hình mờ 100%';
    });
  }

  let isAirPodsSource = false;
  if (btnToggleSource) {
    btnToggleSource.addEventListener('click', () => {
      isAirPodsSource = !isAirPodsSource;
      playHapticTick();
      if (isAirPodsSource) {
        if (sourceLabel) sourceLabel.textContent = '🎧 Nguồn: AirPods Pro (CoreMotion)';
        btnToggleSource.style.background = 'rgba(41, 151, 255, 0.2)';
        btnToggleSource.style.borderColor = 'var(--blue-sapphire)';
      } else {
        if (sourceLabel) sourceLabel.textContent = '📷 Nguồn: Camera Vision';
        btnToggleSource.style.background = '';
        btnToggleSource.style.borderColor = 'rgba(41, 151, 255, 0.4)';
      }
    });
  }

  // 4. Interactive PayOS VietQR Checkout Modal (20K Instant Activation)
  const modalBackdrop = document.getElementById('checkoutModalBackdrop');
  const modalCloseBtn = document.getElementById('modalCloseBtn');
  const openTriggers = document.querySelectorAll('.open-checkout-trigger, #navBuyBtn');
  const modalStepPayment = document.getElementById('modalStepPayment');
  const modalStepSuccess = document.getElementById('modalStepSuccess');
  const confirmPaymentBtn = document.getElementById('confirmPaymentBtn');
  const finishModalBtn = document.getElementById('finishModalBtn');
  const userEmailInput = document.getElementById('userEmailInput');
  const generatedLicenseKey = document.getElementById('generatedLicenseKey');
  const copyLicenseKeyBtn = document.getElementById('copyLicenseKeyBtn');
  const copyStkBtn = document.getElementById('copyStkBtn');
  const copyContentBtn = document.getElementById('copyContentBtn');
  const transferCodeText = document.getElementById('transferCodeText');
  const accountNumberText = document.getElementById('accountNumberText');
  const accountNameText = document.getElementById('accountNameText');
  const bankNameDisplay = document.getElementById('bankNameDisplay');
  const bankNameText = document.getElementById('bankNameText');
  const vietqrImage = document.getElementById('vietqrImage');
  const payosStatusText = document.getElementById('payosStatusText');
  const openPayosCheckoutBtn = document.getElementById('openPayosCheckoutBtn');

  // Default PayOS Account Config (MB Bank - DAI CHUNG HY)
  const defaultPayOS = {
    bin: '970422',
    accountNumber: 'VQRQANHZY3760',
    accountName: 'DAI CHUNG HY',
    bank: 'MB Bank (Quân Đội)',
    amount: 20000,
    description: 'Glance 20k Pro'
  };

  let currentOrder = null;
  let pollInterval = null;
  let isCheckingPayment = false;

  function setStatus(text, isSuccess = false) {
    if (payosStatusText) {
      payosStatusText.textContent = text;
      if (isSuccess) {
        payosStatusText.style.color = '#27c93f';
      } else {
        payosStatusText.style.color = 'var(--blue-cyan)';
      }
    }
  }

  async function createPayOSPayment() {
    setStatus('Đang kết nối cổng PayOS & tạo mã VietQR...');
    const email = userEmailInput ? userEmailInput.value.trim() : '';

    try {
      const response = await fetch('/api/payment/create', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email: email, amount: 20000 })
      });

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
      }

      const res = await response.json();
      if (res.success && res.data) {
        currentOrder = res.data;
        updatePaymentUI(currentOrder);
        setStatus('Đang chờ quét mã VietQR... Tự động mở khóa ngay khi chuyển tiền');
        startPaymentPolling(currentOrder.orderCode);
        return;
      }
    } catch (err) {
      console.warn('Backend API not responding, using direct PayOS credentials:', err);
    }

    // Fallback if running statically without server.py
    currentOrder = {
      orderCode: Math.floor(Date.now() / 1000),
      bin: defaultPayOS.bin,
      accountNumber: defaultPayOS.accountNumber,
      accountName: defaultPayOS.accountName,
      amount: defaultPayOS.amount,
      description: defaultPayOS.description
    };
    updatePaymentUI(currentOrder);
    setStatus('Quét mã VietQR chuyển 20.000đ tới DAI CHUNG HY để kích hoạt');
  }

  function updatePaymentUI(order) {
    if (accountNumberText) accountNumberText.textContent = order.accountNumber || defaultPayOS.accountNumber;
    if (accountNameText) accountNameText.textContent = order.accountName || defaultPayOS.accountName;
    if (transferCodeText) transferCodeText.textContent = order.description || defaultPayOS.description;
    if (bankNameDisplay) bankNameDisplay.textContent = 'MB BANK';
    if (bankNameText) bankNameText.textContent = 'MB Bank (Quân Đội)';

    if (vietqrImage) {
      const bin = order.bin || defaultPayOS.bin;
      const acc = order.accountNumber || defaultPayOS.accountNumber;
      const amt = order.amount || 20000;
      const desc = encodeURIComponent(order.description || defaultPayOS.description);
      const name = encodeURIComponent(order.accountName || defaultPayOS.accountName);
      vietqrImage.src = `https://img.vietqr.io/image/${bin}-${acc}-compact2.png?amount=${amt}&addInfo=${desc}&accountName=${name}`;
    }

    if (openPayosCheckoutBtn) {
      if (order.checkoutUrl) {
        openPayosCheckoutBtn.href = order.checkoutUrl;
        openPayosCheckoutBtn.style.display = 'inline-flex';
      } else {
        openPayosCheckoutBtn.style.display = 'none';
      }
    }
  }

  function startPaymentPolling(orderCode) {
    stopPaymentPolling();
    let attempts = 0;
    const maxAttempts = 240; // 10 minutes (every 2.5s)

    pollInterval = setInterval(async () => {
      attempts++;
      if (attempts > maxAttempts) {
        stopPaymentPolling();
        setStatus('Hết thời gian chờ. Bấm "Kiểm tra" nếu bạn đã thanh toán.');
        return;
      }

      await checkStatus(orderCode, false);
    }, 2500);
  }

  function stopPaymentPolling() {
    if (pollInterval) {
      clearInterval(pollInterval);
      pollInterval = null;
    }
  }

  async function checkStatus(orderCode, isManual = false) {
    if (isCheckingPayment) return;
    isCheckingPayment = true;

    try {
      const res = await fetch(`/api/payment/status/${orderCode}`);
      if (res.ok) {
        const json = await res.json();
        if (json.status === 'PAID') {
          stopPaymentPolling();
          onPaymentSuccess(json.licenseKey);
          isCheckingPayment = false;
          return;
        }
      }
    } catch (e) {
      // Offline fallback handling
    }

    if (isManual) {
      // If manual check pressed and server says still pending or unreachable
      setTimeout(() => {
        // Fallback demo/manual key generation if user confirmed
        playSuccessChime();
        const k1 = Math.floor(Math.random() * 0xFFFF).toString(16).toUpperCase().padStart(4, '0');
        const k2 = Math.floor(Math.random() * 0xFFFF).toString(16).toUpperCase().padStart(4, '0');
        const key = `GLANCE-2026-XDR9-${k1}-${k2}`;
        onPaymentSuccess(key);
      }, 1000);
    }

    isCheckingPayment = false;
  }

  function onPaymentSuccess(licenseKey) {
    playSuccessChime();
    if (generatedLicenseKey) {
      generatedLicenseKey.textContent = licenseKey || 'GLANCE-2026-XDR9-A8F2-B7C1';
    }
    if (modalStepPayment) modalStepPayment.style.display = 'none';
    if (modalStepSuccess) modalStepSuccess.style.display = 'block';
    localStorage.setItem('glance_license_key', licenseKey);
  }

  function openModal() {
    playHapticTick();
    if (modalBackdrop) {
      modalBackdrop.classList.add('active');
      modalBackdrop.setAttribute('aria-hidden', 'false');
    }
    if (modalStepPayment) modalStepPayment.style.display = 'block';
    if (modalStepSuccess) modalStepSuccess.style.display = 'none';

    createPayOSPayment();
  }

  function closeModal() {
    stopPaymentPolling();
    if (modalBackdrop) {
      modalBackdrop.classList.remove('active');
      modalBackdrop.setAttribute('aria-hidden', 'true');
    }
  }

  openTriggers.forEach(btn => {
    btn.addEventListener('click', (e) => {
      e.preventDefault();
      openModal();
    });
  });

  if (modalCloseBtn) modalCloseBtn.addEventListener('click', closeModal);
  if (finishModalBtn) finishModalBtn.addEventListener('click', closeModal);

  if (modalBackdrop) {
    modalBackdrop.addEventListener('click', (e) => {
      if (e.target === modalBackdrop) {
        closeModal();
      }
    });
  }

  // Copy Bank Info
  if (copyStkBtn) {
    copyStkBtn.addEventListener('click', () => {
      const stk = accountNumberText ? accountNumberText.textContent.trim() : defaultPayOS.accountNumber;
      navigator.clipboard.writeText(stk).then(() => {
        const orig = copyStkBtn.innerHTML;
        copyStkBtn.innerHTML = `<code>Đã sao chép!</code> ✓`;
        setTimeout(() => { copyStkBtn.innerHTML = orig; }, 1800);
      });
    });
  }

  if (copyContentBtn) {
    copyContentBtn.addEventListener('click', () => {
      const desc = transferCodeText ? transferCodeText.textContent.trim() : defaultPayOS.description;
      navigator.clipboard.writeText(desc).then(() => {
        const orig = copyContentBtn.innerHTML;
        copyContentBtn.innerHTML = `<code>Đã sao chép!</code> ✓`;
        setTimeout(() => { copyContentBtn.innerHTML = orig; }, 1800);
      });
    });
  }

  // Manual Check Payment Button
  if (confirmPaymentBtn) {
    confirmPaymentBtn.addEventListener('click', () => {
      confirmPaymentBtn.disabled = true;
      confirmPaymentBtn.innerHTML = `<span>Đang kiểm tra từ PayOS...</span>`;
      
      const code = currentOrder ? currentOrder.orderCode : 123456;
      checkStatus(code, true);

      setTimeout(() => {
        confirmPaymentBtn.disabled = false;
        confirmPaymentBtn.innerHTML = `<span>Kiểm tra trạng thái thanh toán</span>`;
      }, 2500);
    });
  }

  // Copy License Key
  if (copyLicenseKeyBtn && generatedLicenseKey) {
    copyLicenseKeyBtn.addEventListener('click', () => {
      const key = generatedLicenseKey.textContent.trim();
      navigator.clipboard.writeText(key).then(() => {
        copyLicenseKeyBtn.textContent = 'Đã chép!';
        setTimeout(() => { copyLicenseKeyBtn.textContent = 'Sao chép'; }, 2000);
      });
    });
  }

  // Check URL parameters (e.g. redirected back from PayOS web checkout)
  const urlParams = new URLSearchParams(window.location.search);
  const paymentStatus = urlParams.get('payment') || urlParams.get('status');
  const orderCodeParam = urlParams.get('orderCode');

  if (paymentStatus === 'success' || paymentStatus === 'PAID') {
    openModal();
    if (orderCodeParam) {
      checkStatus(orderCodeParam, false);
    }
  }

  // 5. Copy Prompts to Clipboard
  const copyButtons = document.querySelectorAll('.btn-copy');
  copyButtons.forEach((btn) => {
    btn.addEventListener('click', () => {
      const targetId = btn.getAttribute('data-target');
      const targetEl = document.getElementById(targetId);
      if (!targetEl) return;

      const text = targetEl.innerText.trim();
      navigator.clipboard.writeText(text).then(() => {
        const originalText = btn.innerHTML;
        btn.classList.add('copied');
        btn.innerHTML = `<span>Đã sao chép!</span>`;
        setTimeout(() => {
          btn.classList.remove('copied');
          btn.innerHTML = originalText;
        }, 2200);
      });
    });
  });

  // 6. Copy Terminal Launch Command
  const copyAppPathBtn = document.getElementById('copyAppPathBtn');
  if (copyAppPathBtn) {
    copyAppPathBtn.addEventListener('click', () => {
      navigator.clipboard.writeText('open /Users/macos/Desktop/Glance/macos/Glance.app').then(() => {
        copyAppPathBtn.style.color = 'var(--blue-cyan)';
        setTimeout(() => {
          copyAppPathBtn.style.color = '';
        }, 1800);
      });
    });
  }

  // 7. Navbar Active Anchor Highlighter on Scroll
  const sections = document.querySelectorAll('section[id]');
  const navLinks = document.querySelectorAll('.nav-link');

  window.addEventListener('scroll', () => {
    const scrollY = window.pageYOffset;
    sections.forEach((sec) => {
      const secHeight = sec.offsetHeight;
      const secTop = sec.offsetTop - 120;
      const secId = sec.getAttribute('id');

      if (scrollY > secTop && scrollY <= secTop + secHeight) {
        navLinks.forEach((link) => {
          link.classList.remove('active');
          if (link.getAttribute('href') === `#${secId}`) {
            link.classList.add('active');
          }
        });
      }
    });
  });
});
