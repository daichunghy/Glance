(() => {
  const buttons = [...document.querySelectorAll('.filter-pill')];
  const rows = [...document.querySelectorAll('.release-row')];
  const status = document.getElementById('filter-status');
  if (!buttons.length || !rows.length) return;

  const LABELS = {
    all: 'toàn bộ',
    mac: 'Mac',
    windows: 'Windows',
    linux: 'Linux',
    web: 'Trang web'
  };

  function applyFilter(filter) {
    let visibleRows = 0;

    rows.forEach(row => {
      const items = [...row.querySelectorAll('.release-items li')];
      let rowMatches = 0;

      items.forEach(item => {
        const platforms = (item.dataset.platforms || '').split(/\s+/);
        const match = filter === 'all' || platforms.includes(filter);
        item.hidden = !match;
        if (match) rowMatches += 1;
      });

      row.hidden = rowMatches === 0;
      if (rowMatches > 0) visibleRows += 1;
    });

    buttons.forEach(btn => {
      const active = btn.dataset.filter === filter;
      btn.classList.toggle('is-active', active);
      btn.setAttribute('aria-pressed', String(active));
    });

    if (status) {
      status.textContent = filter === 'all'
        ? `Đang hiển thị ${LABELS.all} ${visibleRows} mốc cập nhật`
        : `Đang hiển thị ${visibleRows} mốc cập nhật cho ${LABELS[filter] || filter}`;
    }
  }

  buttons.forEach(btn => {
    btn.addEventListener('click', () => applyFilter(btn.dataset.filter));
  });
})();
