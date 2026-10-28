(() => {
  if (!('serviceWorker' in navigator) || !['http:', 'https:'].includes(window.location.protocol)) return;

  window.addEventListener('load', () => {
    navigator.serviceWorker.register('./service-worker.js', { updateViaCache: 'none' }).catch(() => {});
  });
})();
