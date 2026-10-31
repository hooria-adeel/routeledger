// Runs before the page is drawn, so there is no white flash in dark mode
// and the chosen text size is already in place.
(function () {
  var theme = null, size = null;
  try { theme = localStorage.getItem('routeledger-theme'); size = localStorage.getItem('routeledger-size'); } catch (e) {}
  var dark = window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches;
  document.documentElement.setAttribute('data-theme', theme || (dark ? 'dark' : 'light'));
  if (size) document.documentElement.setAttribute('data-size', size);
})();
