export const demoGuide = {
  mount() {
    const status = document.getElementById('demo-guide-status');
    if (status) {
      status.textContent = 'Ready for live walkthrough';
    }
  },
  refresh() {
    // Static demo guide content.
  },
};
