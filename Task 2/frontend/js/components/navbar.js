export function initNavbar() {
  const nav = document.querySelector('.navbar');
  if (!nav) return;
  const settingsButton = nav.querySelector('[data-settings]');
  if (settingsButton) {
    settingsButton.addEventListener('click', () => {
      console.info('Settings button clicked');
    });
  }
}
