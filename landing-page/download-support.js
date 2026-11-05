(() => {
  const downloads = new Map([
    ['Glance-macOS-1.0.0.zip', 'mac'],
    ['Glance-Windows.zip', 'windows']
  ]);
  document.addEventListener('click', event => {
    const link = event.target.closest('a[download]');
    if (!link || event.defaultPrevented || event.button !== 0 || event.metaKey || event.ctrlKey || event.shiftKey || event.altKey) return;
    const file = downloads.get(new URL(link.href).pathname.split('/').pop());
    if (!file) return;
    event.preventDefault();
    location.assign(`ung-ho.html?file=${file}`);
  });
})();
