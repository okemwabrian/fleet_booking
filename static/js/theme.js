(function () {
  const STORAGE_KEY = 'fleet_theme';
  const root = document.documentElement;
  const themeEndpoint = document.body.dataset.themeEndpoint || '';
  const toggleButton = document.getElementById('theme-toggle');
  const themeLabel = document.getElementById('theme-label');

  if (!toggleButton || !themeLabel) {
    return;
  }

  const currentTheme = () => (root.classList.contains('dark') ? 'dark' : 'light');

  const applyThemeLabel = () => {
    themeLabel.textContent = currentTheme() === 'dark' ? 'Dark' : 'Light';
  };

  const setTheme = (theme) => {
    root.classList.toggle('dark', theme === 'dark');
    localStorage.setItem(STORAGE_KEY, theme);
    applyThemeLabel();
    syncThemePreference(theme);
  };

  const getCsrfToken = () => {
    const csrfCookie = document.cookie
      .split(';')
      .map((chunk) => chunk.trim())
      .find((chunk) => chunk.startsWith('csrftoken='));
    return csrfCookie ? decodeURIComponent(csrfCookie.split('=')[1]) : '';
  };

  const syncThemePreference = (theme) => {
    if (!themeEndpoint) return;

    fetch(themeEndpoint, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-CSRFToken': getCsrfToken(),
      },
      credentials: 'same-origin',
      body: JSON.stringify({ theme }),
    }).catch(() => {
      // Ignore sync failures; UI theme remains applied client-side.
    });
  };

  applyThemeLabel();

  toggleButton.addEventListener('click', () => {
    const nextTheme = currentTheme() === 'dark' ? 'light' : 'dark';
    setTheme(nextTheme);
  });
})();
