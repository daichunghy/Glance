(() => {
  const reduced = matchMedia('(prefers-reduced-motion: reduce)');
  const compact = matchMedia('(max-width: 760px)');
  const $ = (selector, root = document) => root.querySelector(selector);
  const template = $('#device-template');
  document.querySelectorAll('[data-device]').forEach(device => {
    device.append(template.content.cloneNode(true));
    const desktop = $('.desktop', device);
    device.querySelectorAll('.privacy-layer').forEach(layer => layer.append(desktop.cloneNode(true)));
  });

  const macDownloads = [...document.querySelectorAll('.download-mac')];
  const windowsDownload = $('.download-windows');
  const requirements = $('#download-requirements');
  const platform = navigator.userAgentData?.platform || navigator.platform || '';
  const agent = navigator.userAgent || '';
  const isWindows = /win/i.test(platform) || /Windows/i.test(agent);
  const isIPad = platform === 'MacIntel' && navigator.maxTouchPoints > 1;
  const isMac = !isIPad && !/iPhone|iPad|iPod/i.test(agent) && (/Mac/i.test(platform) || /Macintosh/i.test(agent));

  if (isWindows) {
    windowsDownload.classList.add('preferred-download');
    requirements.textContent = 'Windows 10 hoặc 11 · Cần Python 3.11 hoặc 3.12';
    document.querySelectorAll('[data-smart-download]').forEach(link => {
      link.href = windowsDownload.href;
      link.setAttribute('download', '');
      link.textContent = 'Tải cho Windows';
    });
  } else if (isMac) {
    macDownloads.forEach(link => link.classList.add('preferred-download'));
    document.querySelectorAll('[data-smart-download]').forEach(link => {
      link.href = macDownloads[0].href;
      link.setAttribute('download', '');
      link.textContent = 'Tải cho Mac Apple silicon';
    });
  } else {
    requirements.textContent = 'Chọn phiên bản phù hợp với máy của bạn.';
  }

  const hero = $('#hero');
  const sequence = $('#sequence');
  const pin = $('.sequence-pin', sequence);
  const device = $('.device', sequence);
  const angle = $('#angle');
  const label = $('#scene-label');
  const track = $('#pods-track');
  const stage = $('#pods-stage');
  const podsPin = $('.pods-pin', track);
  const podsAngle = $('#pods-angle');
  const privacyRun = $('#privacy-run');
  const privacyPin = $('.privacy-pin', privacyRun);
  const rail = $('#privacy-rail');
  const contextFrame = $('#context-frame');

  const chapters = [
    [0, 'Khi bạn nhìn thẳng, cả màn hình đều rõ.'],
    [.19, 'Ứng dụng tự động làm mờ màn hình khi bạn quay mặt đi.'],
    [.55, 'Khi bạn đổi hướng, vùng làm mờ cũng đổi theo.'],
    [.72, 'Màn hình rõ trở lại khi bạn nhìn về giữa.'],
    [.87, 'Ở chế độ camera, Glance có thể che màn hình khi bạn rời chỗ.']
  ];
  const angles = [[0,0],[.10,0],[.24,24],[.36,24],[.47,0],[.59,-24],[.67,-24],[.81,0],[1,0]];
  const clamp = x => Math.max(0, Math.min(1, x));
  const smooth = x => { const t = clamp(x); return t * t * (3 - 2 * t); };
  const ramp = (x, start, end) => smooth((x - start) / (end - start));
  const lerp = (a, b, p) => a + (b - a) * p;

  let scene = -1;
  let frame = 0;
  let lastRail = -1;
  let model;
  let modelLoading = false;
  const near = new Set();
  const sections = [hero, sequence, track, privacyRun, contextFrame];

  function progress(section, sticky) {
    const bounds = section.getBoundingClientRect();
    const top = parseFloat(getComputedStyle(sticky).top) || 0;
    return clamp((top - bounds.top) / Math.max(1, bounds.height - sticky.offsetHeight));
  }

  function yawAt(p) {
    const i = angles.findIndex(([position]) => position >= p);
    if (i <= 0) return 0;
    const [start, a] = angles[i - 1];
    const [end, b] = angles[i];
    return lerp(a, b, ramp(p, start, end));
  }

  function paintSequence(p) {
    const yaw = yawAt(p);
    const cover = ramp(Math.abs(yaw), 20, 24);
    const away = ramp(p, .83, .95);
    const zoom = ramp(p, .04, .27) * (1 - ramp(p, .74, .9));
    const idx = chapters.reduce((current, [at], i) => p >= at ? i : current, 0);
    if (scene !== idx) {
      scene = idx;
      label.textContent = chapters[idx][1];
    }
    const degrees = Math.round(yaw);
    const caption = idx === 4 ? 'Rời bàn' : `${degrees < 0 ? '−' : ''}${Math.abs(degrees)}°`;
    if (angle.textContent !== caption) angle.textContent = caption;
    angle.classList.toggle('is-away', idx === 4);
    const state = away > .65 ? 'away' : cover > .5 ? (yaw > 0 ? 'right' : 'left') : 'center';
    if (device.dataset.state !== state) device.dataset.state = state;
    pin.style.setProperty('--scene-progress', p);
    pin.style.setProperty('--light-x', `${50 + yaw * .42}%`);
    device.style.setProperty('--cover-left', yaw > 0 ? cover : 0);
    device.style.setProperty('--cover-right', yaw < 0 ? cover : 0);
    device.style.setProperty('--cover-full', away);
    device.style.setProperty('--screen-x', `${-yaw * (compact.matches ? .075 : .24)}%`);
    device.style.setProperty('--screen-y', `${(zoom * -1.4 + away * 1.5)}%`);
    device.style.setProperty('--screen-scale', 1 + zoom * (compact.matches ? .14 : .29) + away * .15);
    device.style.setProperty('--screen-turn', `${yaw * -.36}deg`);
  }

  function update() {
    frame = 0;
    if (reduced.matches) {
      paintSequence(.3);
      podsAngle.textContent = '24°';
      if (model) model.draw(.6);
      return;
    }

    if (near.has(hero)) {
      const p = clamp(-hero.getBoundingClientRect().top / Math.max(1, hero.offsetHeight * .56));
      hero.style.setProperty('--hero-copy-y', `${p * 36}px`);
      hero.style.setProperty('--hero-copy-alpha', 1 - ramp(p, .23, .88));
      hero.style.setProperty('--hero-y', `${p * -26}px`);
      hero.style.setProperty('--hero-scale', 1 + p * .21);
      hero.style.setProperty('--hero-tilt', `${p * 9}deg`);
    }
    if (near.has(sequence)) paintSequence(progress(sequence, pin));
    if (near.has(track)) {
      const p = progress(track, podsPin);
      const text = `${Math.round(p * 28)}°`;
      if (podsAngle.textContent !== text) podsAngle.textContent = text;
      stage.style.setProperty('--sensor-reveal', ramp(p, .42, .68));
      stage.style.setProperty('--motion-cover', ramp(p, .52, .74));
      if (model) model.draw(p);
    }
    if (near.has(privacyRun) && !compact.matches) {
      const p = progress(privacyRun, privacyPin);
      const t = ramp(p, .06, .96);
      const shade = Math.round(156 + 88 * ramp(p, 0, .48));
      privacyPin.style.setProperty('--privacy-tone', `${shade} ${shade + 2} ${shade + 6}`);
      if (Math.abs(t - lastRail) > .0001) {
        lastRail = t;
        rail.scrollLeft = (rail.scrollWidth - rail.clientWidth) * t;
      }
    }
    if (near.has(contextFrame)) {
      const bounds = contextFrame.getBoundingClientRect();
      const p = clamp((innerHeight - bounds.top) / (innerHeight + bounds.height));
      contextFrame.style.setProperty('--context-y', `${lerp(-21, 24, p)}px`);
      contextFrame.style.setProperty('--context-scale', lerp(1.14, 1.26, p));
      contextFrame.style.setProperty('--context-copy', `${lerp(25, -14, p)}px`);
      contextFrame.style.setProperty('--context-cover', ramp(p, .24, .48));
    }
  }

  function requestFrame() {
    if (!frame) frame = requestAnimationFrame(update);
  }

  async function loadModel() {
    if (modelLoading || model || reduced.matches || location.protocol === 'file:') return;
    modelLoading = true;
    try {
      const { createPodsScene } = await import('./airpods.js?v=1.9.1');
      model = createPodsScene($('#pods-canvas'), stage);
      model.draw(progress(track, podsPin), true);
      stage.dataset.ready = '';
      new ResizeObserver(() => { if (near.has(track)) requestFrame(); }).observe(stage);
    } catch {
      // Keep the still image when WebGL is unavailable.
    }
  }

  if ('IntersectionObserver' in window) {
    const observer = new IntersectionObserver(entries => {
      entries.forEach(({ target, isIntersecting }) => {
        if (isIntersecting) {
          near.add(target);
          if (target === track) loadModel();
        } else {
          near.delete(target);
        }
      });
      requestFrame();
    }, { rootMargin: '160px' });
    sections.forEach(section => observer.observe(section));
  } else {
    sections.forEach(section => near.add(section));
    loadModel();
  }

  const tour = $('#tour');
  const tourDevice = $('.device', tour);
  const tourText = $('#tour-copy');
  const chip = $('#tour-chip');
  const tourChip = $('span', chip);
  const modes = $('#tour-modes');
  const thresholds = $('#tour-thresholds');
  const topics = {
    side: ['right', '', 'Chế độ làm mờ', 'Chế độ một bên giữ phần bạn đang nhìn rõ nét. Bạn cũng có thể chọn làm mờ toàn màn hình khi quay đầu.'],
    sensitivity: ['right', '', 'Linh hoạt độ nhạy của cảm biến camera', 'Ở góc quay 24°, màn hình sẽ mờ nếu chọn ngưỡng 14° hoặc 20°. Chọn 28° để thấy màn hình vẫn rõ ở cùng góc quay.'],
    away: ['away', 'Chế độ camera', 'Che nội dung khi rời bàn', 'Khi camera không còn thấy bạn và bạn đã ngừng dùng bàn phím hoặc chuột, Glance có thể làm mờ toàn bộ màn hình.'],
    call: ['center', '', 'Màn hình rõ khi gọi video', 'Glance tạm ngừng làm mờ khi Zoom, Teams hoặc FaceTime đang ở phía trước.'],
    align: ['center', '', 'Căn lại hướng nhìn thẳng', 'Nhìn vào giữa màn hình và chọn Calibrate Center trong menu Glance để căn lại hướng nhìn.'],
    input: ['center', '', 'Vẫn rõ khi bạn đang làm việc', 'Nếu camera tạm thời không thấy bạn, màn hình vẫn rõ khi bạn đang dùng bàn phím hoặc chuột.']
  };
  let mode = 'right';
  let threshold = 20;
  const choices = [...tour.querySelectorAll('button[data-topic]')];
  function mark(group, active) {
    group.forEach(button => button.setAttribute('aria-pressed', String(button === active)));
  }
  function renderTour(topic) {
    const [state, tag, headline, text] = topics[topic];
    tour.dataset.topic = topic;
    tour.dataset.threshold = String(threshold);
    tourDevice.dataset.state = topic === 'side' ? mode : topic === 'sensitivity' && threshold > 24 ? 'center' : state;
    chip.hidden = !tag;
    tourChip.textContent = tag;
    modes.hidden = topic !== 'side';
    thresholds.hidden = topic !== 'sensitivity';
    $('strong', tourText).textContent = headline;
    $('p', tourText).textContent = text;
    mark(choices, choices.find(button => button.dataset.topic === topic));
  }
  choices.forEach(button => button.addEventListener('click', () => renderTour(button.dataset.topic)));
  const modeButtons = [...modes.querySelectorAll('button')];
  modeButtons.forEach(button => button.addEventListener('click', () => {
    mode = button.dataset.preview;
    tourDevice.dataset.state = mode;
    mark(modeButtons, button);
  }));
  const thresholdButtons = [...thresholds.querySelectorAll('button')];
  thresholdButtons.forEach(button => button.addEventListener('click', () => {
    threshold = Number(button.dataset.threshold);
    tourDevice.dataset.state = threshold > 24 ? 'center' : 'right';
    tour.dataset.threshold = String(threshold);
    $('#gauge-status').textContent = threshold > 24 ? 'Màn hình rõ' : 'Màn hình mờ';
    mark(thresholdButtons, button);
  }));

  const syncVisibility = () => document.documentElement.classList.toggle('is-page-hidden', document.hidden);
  document.addEventListener('visibilitychange', syncVisibility);
  syncVisibility();

  const animatedCards = document.querySelectorAll('.tile, .scenario-card, .privacy-card, .tour');
  if ('IntersectionObserver' in window) {
    const motionObserver = new IntersectionObserver(entries => {
      entries.forEach(entry => entry.target.classList.toggle('in-view', entry.isIntersecting));
    }, { threshold: 0.15 });
    animatedCards.forEach(card => motionObserver.observe(card));
  } else {
    animatedCards.forEach(card => card.classList.add('in-view'));
  }

  const detail = $('#feature-detail');
  rail.querySelectorAll('.card-more').forEach(button => button.addEventListener('click', () => {
    const card = button.closest('.privacy-card');
    $('#feature-detail-title').textContent = $('h3', card).textContent;
    $('#feature-detail-copy').textContent = $('template', card).content.textContent;
    detail.showModal();
  }));

  addEventListener('scroll', () => { if (!reduced.matches && near.size) requestFrame(); }, { passive: true });
  addEventListener('resize', () => { lastRail = -1; requestFrame(); }, { passive: true });
  reduced.addEventListener('change', () => {
    lastRail = -1;
    if (near.has(track)) loadModel();
    requestFrame();
  });
  requestFrame();
})();
