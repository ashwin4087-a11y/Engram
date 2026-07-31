const DEMO_KEY = 'optivue.demo.walkthrough';

function updateDemoStatus(message) {
  const status = document.getElementById('demo-guide-status');
  if (status) status.textContent = message;
}

export const demoGuide = {
  mount() {
    const stepNodes = Array.from(document.querySelectorAll('[data-step]'));
    const startButton = document.getElementById('btn-demo-start');

    if (!stepNodes.length) return;

    const saved = JSON.parse(localStorage.getItem(DEMO_KEY) || '[]');
    stepNodes.forEach(node => {
      const step = Number(node.dataset.step);
      const isComplete = saved.includes(step);
      node.style.opacity = isComplete ? '0.6' : '1';
      node.style.textDecoration = isComplete ? 'line-through' : 'none';
    });

    if (startButton && !startButton.dataset.bound) {
      startButton.dataset.bound = 'true';
      startButton.addEventListener('click', () => {
        const completed = new Set(JSON.parse(localStorage.getItem(DEMO_KEY) || '[]'));
        stepNodes.forEach((node, index) => {
          completed.add(index + 1);
          node.style.opacity = '0.6';
          node.style.textDecoration = 'line-through';
        });
        localStorage.setItem(DEMO_KEY, JSON.stringify(Array.from(completed)));
        updateDemoStatus('Walkthrough completed for the live demo sequence');
      });
    }

    updateDemoStatus('Ready for live walkthrough');
  },
  refresh() {
    this.mount();
  },
};
