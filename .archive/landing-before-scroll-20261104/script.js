(() => {
  const reduced = matchMedia('(prefers-reduced-motion: reduce)');
  const template = document.getElementById('device-template');
  document.querySelectorAll('[data-device]').forEach(device => {
    device.append(template.content.cloneNode(true));
    const desktop = device.querySelector('.desktop');
    device.querySelectorAll('.privacy-layer').forEach(veil => veil.append(desktop.cloneNode(true)));
  });

  const sequence = document.getElementById('sequence');
  const pin = sequence.querySelector('.sequence-pin');
  const device = sequence.querySelector('.device');
  const angle = document.getElementById('angle');
  const label = document.getElementById('scene-label');
  const timeline = Array.from(sequence.querySelectorAll('.timeline i'));
  const track = document.getElementById('pods-track');
  const stage = document.getElementById('pods-stage');
  const podsPin = track.querySelector('.pods-pin');
  const podsAngle = document.getElementById('pods-angle');
  const scenes = [
    ['center', '0°', 'Khi bạn nhìn thẳng, cả màn hình đều rõ.'],
    ['right', '24°', 'Glance làm mờ phần màn hình ngoài hướng nhìn.'],
    ['left', '−24°', 'Khi bạn đổi hướng, vùng làm mờ cũng đổi theo.'],
    ['center', '0°', 'Màn hình rõ trở lại khi bạn nhìn về giữa.'],
    ['away', 'Rời bàn', 'Glance làm mờ cả màn hình khi bạn ra khỏi khung hình.']
  ];

  let scene = -1;
  let frame = 0;
  let podsVisible = false;
  let sequenceVisible = true;
  let model;
  let modelLoading = false;

  function progress(section, sticky) {
    const bounds = section.getBoundingClientRect();
    const top = parseFloat(getComputedStyle(sticky).top) || 0;
    const distance = Math.max(1, bounds.height - sticky.offsetHeight);
    return Math.max(0, Math.min(1, (top - bounds.top) / distance));
  }

  function showScene(index) {
    if (index === scene) return;
    scene = index;
    const [state, degrees, caption] = scenes[index];
    device.dataset.state = state;
    angle.textContent = degrees;
    angle.classList.toggle('is-away', state === 'away');
    label.textContent = caption;
    timeline.forEach((dot, i) => dot.classList.toggle('active', i === index));
  }

  function update() {
    frame = 0;
    if (reduced.matches) {
      showScene(1);
      podsAngle.textContent = '24°';
      if (model) model.draw(.6);
      return;
    }
    if (sequenceVisible) showScene(Math.min(scenes.length - 1, Math.floor(progress(sequence, pin) * scenes.length)));
    if (podsVisible) {
      const p = progress(track, podsPin);
      const degrees = Math.round(p * 28);
      podsAngle.textContent = `${degrees}°`;
      if (model) model.draw(p);
    }
  }

  function requestFrame() {
    if (!frame) frame = requestAnimationFrame(update);
  }

  async function loadModel() {
    if (modelLoading || model || reduced.matches || location.protocol === 'file:') return;
    modelLoading = true;
    try {
      const { createPodsScene } = await import('./airpods.js');
      model = createPodsScene(document.getElementById('pods-canvas'), stage);
      model.draw(progress(track, podsPin), true);
      stage.dataset.ready = '';
      new ResizeObserver(() => { if (podsVisible) requestFrame(); }).observe(stage);
    } catch {
      // The static illustration stays in place if WebGL is unavailable.
    }
  }

  if ('IntersectionObserver' in window) {
    new IntersectionObserver(([entry]) => {
      podsVisible = entry.isIntersecting;
      if (podsVisible) loadModel();
      requestFrame();
    }, { rootMargin: '120px' }).observe(track);
    new IntersectionObserver(([entry]) => {
      sequenceVisible = entry.isIntersecting;
      requestFrame();
    }, { rootMargin: '120px' }).observe(sequence);
  } else {
    podsVisible = true;
    loadModel();
  }

  addEventListener('scroll', () => { if (!reduced.matches && (podsVisible || sequenceVisible)) requestFrame(); }, { passive: true });
  addEventListener('resize', requestFrame, { passive: true });
  reduced.addEventListener('change', () => {
    if (podsVisible) loadModel();
    requestFrame();
  });
  requestFrame();
})();
