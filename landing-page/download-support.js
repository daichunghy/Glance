(() => {
  const downloads = new Map([
    ['Glance-macOS-1.0.2.zip', 'mac'],
    ['Glance-Windows.zip', 'windows']
  ]);
  document.addEventListener('click', event => {
    const link = event.target.closest('a[download]');
    if (!link || event.defaultPrevented || event.button !== 0 || event.metaKey || event.ctrlKey || event.shiftKey || event.altKey) return;
    const fileUrl = new URL(link.href, location.href);
    const file = downloads.get(fileUrl.pathname.split('/').pop());
    if (!file) return;
    // A cross-origin file cannot be started later without a click. Let this
    // click download it. Same-origin files still pass through the support page.
    if (fileUrl.origin !== location.origin) return;
    event.preventDefault();
    location.assign(`ung-ho.html?file=${file}`);
  });
})();
