(() => {
  /* ==========================================================================
     1. 60FPS REACTIVE MASCOT CANVAS ENGINE (SPRITE + EMOTIONS + SPRING PHYSICS)
     ========================================================================== */
  const stage = document.getElementById('apple-art-stage');
  const frameBox = document.getElementById('mascot-stage');
  const canvas = document.getElementById('mascot-canvas');
  const moodPill = document.getElementById('mascot-mood');
  const moodEmojiEl = moodPill?.querySelector('.mood-emoji');
  const moodTextEl = moodPill?.querySelector('.mood-text');
  const reducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)');

  const MOODS = {
    idle: {
      emoji: '☕',
      text: 'Chọn ly cà phê bạn thích nha!',
      gaze: 0.44,
      scale: 1,
      tilt: 0,
      blush: 0,
      eyeSparkle: 0.15
    },
    cool: {
      emoji: '🍵',
      text: 'Mát ruột liền, cảm ơn bạn!',
      gaze: 0.16,
      scale: 1.018,
      tilt: -0.8,
      blush: 0.12,
      eyeSparkle: 0.35
    },
    cozy: {
      emoji: '☕',
      text: 'Đủ tỉnh táo sửa bug xuyên ngày!',
      gaze: 0.16,
      scale: 1.022,
      tilt: -1.1,
      blush: 0.22,
      eyeSparkle: 0.45
    },
    happy: {
      emoji: '🥐',
      text: 'Ấm bụng quá trời luôn nè!',
      gaze: 0.14,
      scale: 1.032,
      tilt: -1.6,
      blush: 0.45,
      eyeSparkle: 0.72
    },
    overjoyed: {
      emoji: '🚀',
      text: 'Quá đỉnh! Cảm ơn bạn siêu nhiều!',
      gaze: 0.12,
      scale: 1.045,
      tilt: -2.1,
      blush: 0.68,
      eyeSparkle: 1
    },
    love: {
      emoji: '💙',
      text: 'Chốt đơn ly này với mình nha!',
      gaze: 0.10,
      scale: 1.05,
      tilt: -2.2,
      blush: 0.72,
      eyeSparkle: 1
    },
    curious: {
      emoji: '👀',
      text: 'Con số nào cũng quý hết á!',
      gaze: 0.18,
      scale: 1.025,
      tilt: -2.6,
      blush: 0.18,
      eyeSparkle: 0.55
    },
    sweet: {
      emoji: '👋',
      text: 'Không sao đâu, dùng Glance vui nhé!',
      gaze: 0.36,
      scale: 0.995,
      tilt: 2.2,
      blush: 0.1,
      eyeSparkle: 0.2
    }
  };

  let activeMoodKey = 'cozy';
  let hoverMoodKey = null;
  let selectedMoodKey = 'cozy';
  let mascotApi = null;

  function applyMood(key, opts = {}) {
    const cfg = MOODS[key] || MOODS.idle;
    activeMoodKey = key;
    if (stage) stage.dataset.mood = key;
    if (moodEmojiEl && moodTextEl) {
      const nextText = opts.customText || cfg.text;
      const nextEmoji = opts.customEmoji || cfg.emoji;
      if (moodEmojiEl.textContent !== nextEmoji || moodTextEl.textContent !== nextText) {
        moodEmojiEl.textContent = nextEmoji;
        moodTextEl.textContent = nextText;
        if (moodPill) {
          moodPill.classList.remove('is-pop');
          void moodPill.offsetWidth;
          moodPill.classList.add('is-pop');
        }
      }
    }
    if (mascotApi && opts.bounce) mascotApi.triggerBounce(opts.bounce);
    if (mascotApi && opts.burst) mascotApi.burstParticles(opts.burst, key);
  }

  if (canvas) {
    const ctx = canvas.getContext('2d');
    const COLS = 6;
    const ROWS = 10;
    const TOTAL_FRAMES = COLS * ROWS; // 60 frames
    const FRAME_W = 560;
    const FRAME_H = 315;

    const sprite = new Image();
    sprite.decoding = 'async';
    sprite.src = 'assets/product/glance-scrub-sprite.webp';

    let spriteReady = false;
    sprite.addEventListener('load', () => {
      spriteReady = true;
    });
    if (sprite.complete && sprite.naturalWidth > 0) {
      spriteReady = true;
    }

    // Spring state
    let gaze = 0.22;
    let gazeVel = 0;
    let pointerGaze = null;
    let pointerActive = false;
    let pointerIdleTimer = null;

    let scale = 1.02;
    let scaleVel = 0;
    let tilt = 0;
    let tiltVel = 0;
    let bounceY = 0;
    let bounceVel = 0;
    let blushAlpha = 0;
    let sparkleAlpha = 0.25;

    const particles = [];

    function spawnParticle(mode, burst = false) {
      if (reducedMotion.matches || particles.length > 34) return;
      const xBase = burst ? FRAME_W * (0.28 + Math.random() * 0.48) : FRAME_W * (0.48 + Math.random() * 0.44);
      const yBase = burst ? FRAME_H * (0.35 + Math.random() * 0.45) : FRAME_H * (0.78 + Math.random() * 0.2);
      let kind = 'dot';
      let color = '#80bfff';
      let size = 3 + Math.random() * 3.5;
      let vx = (Math.random() - 0.5) * (burst ? 2.4 : 0.45);
      let vy = -(0.55 + Math.random() * (burst ? 2.2 : 0.9));

      if (mode === 'love') {
        kind = Math.random() < 0.6 ? 'heart' : 'star';
        color = Math.random() < 0.65 ? '#ff7eb6' : '#80bfff';
        size = 6 + Math.random() * 5;
      } else if (mode === 'overjoyed') {
        kind = 'star';
        color = Math.random() < 0.55 ? '#ffd166' : '#80bfff';
        size = 5 + Math.random() * 5;
      } else if (mode === 'happy') {
        kind = Math.random() < 0.4 ? 'star' : 'dot';
        color = Math.random() < 0.6 ? '#fbbf24' : '#93c5fd';
        size = 4 + Math.random() * 4;
      } else if (mode === 'cozy') {
        kind = 'steam';
        color = 'rgba(255, 224, 178, 0.75)';
        size = 7 + Math.random() * 6;
        vy = -(0.45 + Math.random() * 0.5);
      } else if (mode === 'cool') {
        kind = 'dot';
        color = '#67e8f9';
        size = 3 + Math.random() * 3.5;
      }

      particles.push({
        x: xBase,
        y: yBase,
        vx,
        vy,
        size,
        kind,
        color,
        life: 0,
        maxLife: burst ? 55 + Math.random() * 35 : 70 + Math.random() * 50,
        phase: Math.random() * Math.PI * 2
      });
    }

    function lerp(a, b, t) {
      return a + (b - a) * t;
    }

    // Tracked eye & cheek UVs across gaze [0 = right, 0.5 = center, 1 = left]
    function faceAnchors(g) {
      const clamped = Math.max(0, Math.min(1, g));
      let t;
      let a;
      let b;
      if (clamped <= 0.5) {
        t = clamped * 2;
        a = { lx: 0.295, ly: 0.445, rx: 0.365, ry: 0.445, clx: 0.275, cly: 0.565, crx: 0.380, cry: 0.560 };
        b = { lx: 0.255, ly: 0.445, rx: 0.320, ry: 0.445, clx: 0.235, cly: 0.565, crx: 0.345, cry: 0.560 };
      } else {
        t = (clamped - 0.5) * 2;
        a = { lx: 0.255, ly: 0.445, rx: 0.320, ry: 0.445, clx: 0.235, cly: 0.565, crx: 0.345, cry: 0.560 };
        b = { lx: 0.220, ly: 0.440, rx: 0.275, ry: 0.440, clx: 0.205, cly: 0.555, crx: 0.315, cry: 0.555 };
      }
      return {
        lx: lerp(a.lx, b.lx, t) * FRAME_W,
        ly: lerp(a.ly, b.ly, t) * FRAME_H,
        rx: lerp(a.rx, b.rx, t) * FRAME_W,
        ry: lerp(a.ry, b.ry, t) * FRAME_H,
        clx: lerp(a.clx, b.clx, t) * FRAME_W,
        cly: lerp(a.cly, b.cly, t) * FRAME_H,
        crx: lerp(a.crx, b.crx, t) * FRAME_W,
        cry: lerp(a.cry, b.cry, t) * FRAME_H
      };
    }

    function drawStar(cx, cy, r, alpha, color = '#ffffff') {
      if (alpha <= 0.01) return;
      ctx.save();
      ctx.globalAlpha = alpha;
      ctx.fillStyle = color;
      ctx.translate(cx, cy);
      ctx.beginPath();
      for (let i = 0; i < 4; i++) {
        const angle = (i * Math.PI) / 2;
        ctx.lineTo(Math.cos(angle) * r, Math.sin(angle) * r);
        ctx.lineTo(Math.cos(angle + Math.PI / 4) * (r * 0.28), Math.sin(angle + Math.PI / 4) * (r * 0.28));
      }
      ctx.closePath();
      ctx.fill();
      ctx.restore();
    }

    function drawHeart(cx, cy, size, alpha, color) {
      ctx.save();
      ctx.globalAlpha = alpha;
      ctx.fillStyle = color;
      ctx.translate(cx, cy);
      ctx.beginPath();
      const s = size * 0.55;
      ctx.moveTo(0, s * 0.45);
      ctx.bezierCurveTo(s * 0.9, -s * 0.4, s * 1.45, s * 0.55, 0, s * 1.45);
      ctx.bezierCurveTo(-s * 1.45, s * 0.55, -s * 0.9, -s * 0.4, 0, s * 0.45);
      ctx.fill();
      ctx.restore();
    }

    function drawFrame(index, alpha) {
      const idx = Math.max(0, Math.min(TOTAL_FRAMES - 1, index));
      const col = idx % COLS;
      const row = Math.floor(idx / COLS);
      ctx.globalAlpha = alpha;
      ctx.drawImage(
        sprite,
        col * FRAME_W,
        row * FRAME_H,
        FRAME_W,
        FRAME_H,
        0,
        0,
        FRAME_W,
        FRAME_H
      );
    }

    mascotApi = {
      triggerBounce(strength = -2.4) {
        if (!reducedMotion.matches) {
          bounceVel += strength;
          scaleVel += 0.008;
        }
      },
      burstParticles(count = 10, mode = activeMoodKey) {
        for (let i = 0; i < count; i++) {
          spawnParticle(mode, true);
        }
      }
    };

    function onPointerMove(clientX, clientY) {
      pointerActive = true;
      if (frameBox) {
        const rect = frameBox.getBoundingClientRect();
        const centerX = rect.left + rect.width * 0.36; // centered on character face
        // Right of face -> look right (gaze -> 0.08..0.3), Left of face -> look left (gaze -> 0.65..0.92)
        const dx = (clientX - centerX) / Math.max(240, window.innerWidth * 0.55);
        pointerGaze = Math.max(0.05, Math.min(0.95, 0.46 - dx * 0.42));
        const dy = Math.max(-1, Math.min(1, (clientY - (rect.top + rect.height * 0.5)) / 360));
        if (!hoverMoodKey) {
          tilt = lerp(tilt, dy * 1.3, 0.2);
        }
      }
      clearTimeout(pointerIdleTimer);
      pointerIdleTimer = setTimeout(() => {
        pointerActive = false;
        pointerGaze = null;
      }, 1700);
    }

    window.addEventListener('mousemove', e => onPointerMove(e.clientX, e.clientY), { passive: true });
    window.addEventListener('touchmove', e => {
      if (e.touches.length > 0) onPointerMove(e.touches[0].clientX, e.touches[0].clientY);
    }, { passive: true });

    // Interactive click/tap on mascot itself gives a friendly hop & sparkle
    if (frameBox) {
      frameBox.addEventListener('click', () => {
        mascotApi.triggerBounce(-3.2);
        mascotApi.burstParticles(12, activeMoodKey);
        applyMood(activeMoodKey, { customEmoji: '✨', customText: 'Hehe, cảm ơn bạn đã ghé Glance!' });
      });
    }

    let lastTick = performance.now();
    let ambientTimer = 0;

    function render(now) {
      const dt = Math.min(0.05, (now - lastTick) / 1000);
      lastTick = now;

      const mood = MOODS[activeMoodKey] || MOODS.idle;
      const breath = reducedMotion.matches ? 0 : Math.sin(now * 0.0022) * 1.8;
      const idleSway = reducedMotion.matches ? 0 : Math.sin(now * 0.0011) * 0.06;

      // Determine gaze target: hover overrides pointer, pointer overrides idle sway
      let targetGaze = mood.gaze + idleSway;
      if (!hoverMoodKey && pointerActive && pointerGaze !== null) {
        targetGaze = pointerGaze;
      }
      targetGaze = Math.max(0.02, Math.min(0.98, targetGaze));

      // Damped spring integration
      if (reducedMotion.matches) {
        gaze = targetGaze;
        scale = mood.scale;
        tilt = mood.tilt;
        bounceY = 0;
      } else {
        const gForce = (targetGaze - gaze) * 55;
        gazeVel = (gazeVel + gForce * dt) * Math.exp(-14 * dt);
        gaze += gazeVel * dt;
        gaze = Math.max(0, Math.min(1, gaze));

        const sTarget = mood.scale + (hoverMoodKey ? 0.01 : 0);
        const sForce = (sTarget - scale) * 65;
        scaleVel = (scaleVel + sForce * dt) * Math.exp(-13 * dt);
        scale += scaleVel * dt;

        const tForce = (mood.tilt - tilt) * 55;
        tiltVel = (tiltVel + tForce * dt) * Math.exp(-13 * dt);
        tilt += tiltVel * dt;

        const bForce = -bounceY * 140;
        bounceVel = (bounceVel + bForce * dt) * Math.exp(-11 * dt);
        bounceY += bounceVel * dt * 60;
      }

      blushAlpha = lerp(blushAlpha, mood.blush, Math.min(1, dt * 6));
      sparkleAlpha = lerp(sparkleAlpha, mood.eyeSparkle, Math.min(1, dt * 6));

      // Ambient particle spawning based on emotion
      ambientTimer += dt;
      const spawnRate = activeMoodKey === 'love' || activeMoodKey === 'overjoyed'
        ? 0.14
        : activeMoodKey === 'happy' || activeMoodKey === 'cozy'
          ? 0.24
          : activeMoodKey === 'cool'
            ? 0.32
            : 999;
      if (ambientTimer >= spawnRate) {
        ambientTimer = 0;
        spawnParticle(activeMoodKey, false);
      }

      ctx.clearRect(0, 0, FRAME_W, FRAME_H);

      if (spriteReady) {
        ctx.save();
        // Slight overscan (1.035) keeps tilted corners cleanly filled
        const drawScale = scale * 1.035;
        ctx.translate(FRAME_W * 0.5, FRAME_H * 0.5 + breath + bounceY);
        ctx.rotate((tilt * Math.PI) / 180);
        ctx.scale(drawScale, drawScale);
        ctx.translate(-FRAME_W * 0.5, -FRAME_H * 0.5);

        // Sub-frame crossfade for silky 60/120fps motion
        const frameFloat = gaze * (TOTAL_FRAMES - 1);
        const f0 = Math.floor(frameFloat);
        const f1 = Math.min(TOTAL_FRAMES - 1, f0 + 1);
        const frac = frameFloat - f0;

        drawFrame(f0, 1);
        if (frac > 0.01 && f1 !== f0) {
          drawFrame(f1, frac);
        }
        ctx.globalAlpha = 1;

        const face = faceAnchors(gaze);

        // Tracked warm rosy cheek blush
        if (blushAlpha > 0.02) {
          for (const [cx, cy] of [[face.clx, face.cly], [face.crx, face.cry]]) {
            const grad = ctx.createRadialGradient(cx, cy, 2, cx, cy, 22);
            grad.addColorStop(0, `rgba(255, 108, 145, ${blushAlpha * 0.42})`);
            grad.addColorStop(1, 'rgba(255, 108, 145, 0)');
            ctx.fillStyle = grad;
            ctx.beginPath();
            ctx.arc(cx, cy, 22, 0, Math.PI * 2);
            ctx.fill();
          }
        }

        // Tracked eye twinkle glints
        if (sparkleAlpha > 0.05) {
          const pulse = 0.78 + 0.22 * Math.sin(now * 0.008);
          const r = 4.2 + sparkleAlpha * 3.8;
          drawStar(face.lx - 3, face.ly - 3, r * pulse, sparkleAlpha * 0.9, '#ffffff');
          drawStar(face.rx - 3, face.ry - 3, r * pulse, sparkleAlpha * 0.9, '#ffffff');
        }

        ctx.restore();
      }

      // Render & update ambient particles
      for (let i = particles.length - 1; i >= 0; i--) {
        const p = particles[i];
        p.life += 1;
        p.x += p.vx + Math.sin(now * 0.004 + p.phase) * 0.25;
        p.y += p.vy;
        const progress = p.life / p.maxLife;
        if (progress >= 1) {
          particles.splice(i, 1);
          continue;
        }
        const fade = progress < 0.2 ? progress / 0.2 : 1 - (progress - 0.2) / 0.8;
        if (p.kind === 'heart') {
          drawHeart(p.x, p.y, p.size, fade * 0.85, p.color);
        } else if (p.kind === 'star') {
          drawStar(p.x, p.y, p.size, fade * 0.92, p.color);
        } else if (p.kind === 'steam') {
          ctx.save();
          ctx.globalAlpha = fade * 0.35;
          ctx.strokeStyle = p.color;
          ctx.lineWidth = 2;
          ctx.lineCap = 'round';
          ctx.beginPath();
          ctx.moveTo(p.x, p.y);
          ctx.quadraticCurveTo(p.x + Math.sin(now * 0.005 + p.phase) * 8, p.y - 10, p.x, p.y - 20);
          ctx.stroke();
          ctx.restore();
        } else {
          ctx.save();
          ctx.globalAlpha = fade * 0.75;
          ctx.fillStyle = p.color;
          ctx.beginPath();
          ctx.arc(p.x, p.y, p.size * 0.5, 0, Math.PI * 2);
          ctx.fill();
          ctx.restore();
        }
      }

      requestAnimationFrame(render);
    }

    requestAnimationFrame(render);
  }

  /* ==========================================================================
     2. DOWNLOADS & PAYOS DONATION LOGIC (WITH COMMA FORMATTING)
     ========================================================================== */
  const files = {
    mac: 'assets/product/Glance-macOS-1.0.0.zip',
    windows: 'https://github.com/daichunghy/Glance/releases/download/v1.0.0/Glance-Windows.zip'
  };
  const params = new URLSearchParams(location.search);
  const file = Object.hasOwn(files, params.get('file')) ? params.get('file') : null;
  const manual = document.getElementById('manual-download');

  if (file && manual) {
    manual.href = files[file];
    const notice = document.getElementById('download-notice');
    if (notice) notice.hidden = false;
    const target = new URL(manual.href, location.href);
    const msg = document.getElementById('download-message');
    if (target.origin !== location.origin) {
      if (msg) msg.textContent = 'Bấm Tải lại nếu file Glance chưa xuất hiện trong thư mục Tải về.';
      return;
    }
    if (!params.has('support')) {
      manual.click();
    } else if (msg) {
      msg.textContent = 'Bạn đã chọn bản cài đặt Glance.';
    }
  }

  const form = document.getElementById('support-form');
  if (!form) return;

  const amount = document.getElementById('support-amount');
  const status = document.getElementById('support-status');
  const button = document.getElementById('submit-btn');
  const btnText = button.querySelector('.btn-text');
  const noteBox = document.getElementById('preset-note');
  const skipLink = document.getElementById('skip-link');
  const presets = [...form.querySelectorAll('input[name="preset"]')];
  const pillLabels = [...form.querySelectorAll('.apple-pill')];

  function formatVnd(num) {
    if (!Number.isFinite(num) || num <= 0) return '';
    return Math.trunc(num).toString().replace(/\B(?=(\d{3})+(?!\d))/g, ',');
  }

  function parseVnd(raw) {
    const digits = String(raw || '').replace(/[^\d]/g, '');
    if (!digits) return NaN;
    return Number(digits);
  }

  function moodForAmount(val) {
    if (!Number.isFinite(val)) return 'curious';
    if (val >= 100000) return 'overjoyed';
    if (val >= 50000) return 'happy';
    if (val >= 20000) return 'cozy';
    return 'cool';
  }

  function updateButtonLabel(val) {
    if (!btnText) return;
    if (Number.isFinite(val) && val >= 1000) {
      btnText.textContent = `Ủng hộ ${formatVnd(val)}đ qua PayOS ☕`;
    } else {
      btnText.textContent = 'Ủng hộ qua PayOS ☕';
    }
  }

  function validateAmountInput(val) {
    if (!Number.isFinite(val)) {
      amount.setCustomValidity('Vui lòng nhập số tiền bạn muốn ủng hộ.');
      return false;
    }
    if (val < 1000) {
      amount.setCustomValidity('Số tiền ủng hộ tối thiểu là 1,000đ.');
      return false;
    }
    if (val > 100000000) {
      amount.setCustomValidity('Số tiền ủng hộ tối đa là 100,000,000đ.');
      return false;
    }
    amount.setCustomValidity('');
    return true;
  }

  // Format initial value cleanly with commas
  const initialVal = parseVnd(amount.value);
  if (Number.isFinite(initialVal)) {
    amount.value = formatVnd(initialVal);
    updateButtonLabel(initialVal);
    selectedMoodKey = moodForAmount(initialVal);
    applyMood(selectedMoodKey);
  }

  // Preset switching + expressive hover reactions
  presets.forEach((preset, idx) => {
    const pill = pillLabels[idx];
    const pillMood = pill?.dataset.mood || moodForAmount(Number(preset.value));

    preset.addEventListener('change', () => {
      if (preset.checked) {
        const val = Number(preset.value);
        amount.value = formatVnd(val);
        validateAmountInput(val);
        updateButtonLabel(val);
        pillLabels.forEach(p => p.classList.remove('is-selected'));
        pill?.classList.add('is-selected');
        selectedMoodKey = pillMood;
        applyMood(pillMood, { bounce: -2.4, burst: 6 });

        const note = preset.dataset.note;
        if (note && noteBox) noteBox.textContent = note;
      }
    });

    if (pill) {
      pill.addEventListener('mouseenter', () => {
        hoverMoodKey = pillMood;
        applyMood(pillMood, { bounce: -1.6 });
      });
      pill.addEventListener('mouseleave', () => {
        if (hoverMoodKey === pillMood) {
          hoverMoodKey = null;
          applyMood(selectedMoodKey);
        }
      });
      pill.addEventListener('focusin', () => {
        hoverMoodKey = pillMood;
        applyMood(pillMood, { bounce: -1.4 });
      });
      pill.addEventListener('focusout', () => {
        if (hoverMoodKey === pillMood) {
          hoverMoodKey = null;
          applyMood(selectedMoodKey);
        }
      });
    }
  });

  // Custom amount live comma formatting + caret preservation + mascot reaction
  amount.addEventListener('input', () => {
    const raw = amount.value;
    const caret = amount.selectionStart ?? raw.length;
    const digitsBeforeCaret = raw.slice(0, caret).replace(/[^\d]/g, '').length;
    const digitsOnly = raw.replace(/[^\d]/g, '').slice(0, 9);
    const numeric = digitsOnly ? Number(digitsOnly) : NaN;
    const formatted = digitsOnly ? formatVnd(numeric) : '';

    amount.value = formatted;

    // Restore cursor after the same number of digits
    let nextPos = 0;
    let seen = 0;
    while (nextPos < formatted.length && seen < digitsBeforeCaret) {
      if (/\d/.test(formatted[nextPos])) seen += 1;
      nextPos += 1;
    }
    try {
      amount.setSelectionRange(nextPos, nextPos);
    } catch {
      // Ignore selection error on unsupported input types
    }

    validateAmountInput(numeric);
    updateButtonLabel(numeric);

    let matched = false;
    presets.forEach((preset, idx) => {
      if (Number.isFinite(numeric) && Number(preset.value) === numeric) {
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

    if (Number.isFinite(numeric)) {
      selectedMoodKey = moodForAmount(numeric);
      if (numeric < 1000) {
        applyMood('curious', { customEmoji: '😅', customText: 'Tối thiểu 1,000đ nha bạn!' });
      } else {
        applyMood(selectedMoodKey, {
          customText: numeric >= 100000
            ? `${formatVnd(numeric)}đ luôn hả?! Quá đỉnh! 💙`
            : `${formatVnd(numeric)}đ — Cảm ơn tấm lòng của bạn!`
        });
      }
    } else {
      applyMood('curious');
    }
  });

  amount.addEventListener('focus', () => {
    hoverMoodKey = 'curious';
    const val = parseVnd(amount.value);
    applyMood(Number.isFinite(val) && val >= 50000 ? moodForAmount(val) : 'curious', { bounce: -1.2 });
  });

  amount.addEventListener('blur', () => {
    if (hoverMoodKey === 'curious') {
      hoverMoodKey = null;
      applyMood(selectedMoodKey);
    }
  });

  // Expressive hover reactions on Main Donate Button
  button.addEventListener('mouseenter', () => {
    hoverMoodKey = 'love';
    const val = parseVnd(amount.value);
    const label = Number.isFinite(val) && val >= 1000 ? `Chốt ${formatVnd(val)}đ với mình nha!` : MOODS.love.text;
    applyMood('love', { bounce: -2.2, burst: 5, customText: label });
  });
  button.addEventListener('mouseleave', () => {
    if (hoverMoodKey === 'love') {
      hoverMoodKey = null;
      applyMood(selectedMoodKey);
    }
  });
  button.addEventListener('focus', () => {
    hoverMoodKey = 'love';
    applyMood('love', { bounce: -1.5 });
  });
  button.addEventListener('blur', () => {
    if (hoverMoodKey === 'love') {
      hoverMoodKey = null;
      applyMood(selectedMoodKey);
    }
  });

  // Gentle understanding reaction on Skip link
  if (skipLink) {
    skipLink.addEventListener('mouseenter', () => {
      hoverMoodKey = 'sweet';
      applyMood('sweet');
    });
    skipLink.addEventListener('mouseleave', () => {
      if (hoverMoodKey === 'sweet') {
        hoverMoodKey = null;
        applyMood(selectedMoodKey);
      }
    });
  }

  // Status message from PayOS return
  if (params.get('support') === 'return') {
    status.style.color = '#2ed573';
    status.textContent = 'Cảm ơn tấm lòng của bạn! Món quà tiếp sức đã được ghi nhận. 💙';
    selectedMoodKey = 'love';
    applyMood('love', { bounce: -3.5, burst: 18, customEmoji: '🥳', customText: 'Cảm ơn bạn rất nhiều luôn!!' });
  } else if (params.get('support') === 'cancel') {
    status.style.color = '#b5b6bc';
    status.textContent = 'Bạn đã hủy lượt tiếp sức. Chúc bạn có trải nghiệm tuyệt vời với Glance!';
    selectedMoodKey = 'sweet';
    applyMood('sweet');
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
    const numericAmount = parseVnd(amount.value);
    if (!validateAmountInput(numericAmount) || !form.reportValidity()) return;

    button.disabled = true;
    if (btnText) btnText.textContent = 'Đang mở cổng PayOS…';
    status.textContent = '';
    applyMood('love', { bounce: -2.8, burst: 14, customEmoji: '🚀', customText: 'Đang kết nối PayOS cho bạn nè…' });

    try {
      if (isConfigured === false) {
        throw new Error('CONFIG_DISABLED');
      }

      const response = await fetch('/api/donation/create', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ amount: numericAmount, file })
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
      updateButtonLabel(numericAmount);
    }
  });
})();