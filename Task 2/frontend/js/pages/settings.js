export const settings = {
  mount() {
    const status = document.getElementById('settings-status');
    if (status) {
      status.textContent = 'Connected';
    }
  },
  refresh() {
    // Static settings content.
  },
};
