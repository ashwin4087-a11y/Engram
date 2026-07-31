import { initRouter } from './router.js';
import { pageHandlers } from './pages/index.js';
import { POLL_INTERVAL_MS } from './config.js';

const elements = {
  navLinks: Array.from(document.querySelectorAll('.nav-link')),
  pageSections: {
    dashboard: document.getElementById('page-dashboard'),
    calibration: document.getElementById('page-calibration'),
    analytics: document.getElementById('page-analytics'),
    evaluation: document.getElementById('page-evaluation'),
    architecture: document.getElementById('page-architecture'),
    demoGuide: document.getElementById('page-demoGuide'),
    settings: document.getElementById('page-settings'),
    about: document.getElementById('page-about'),
  },
  backendStatusDot: document.getElementById('backend-status-dot'),
};

let pollers = [];

function clearPollers() {
  pollers.forEach(clearInterval);
  pollers = [];
}

function setBackendStatus(connected) {
  if (!elements.backendStatusDot) return;
  elements.backendStatusDot.className = connected
    ? 'w-2 h-2 rounded-full bg-emerald-500'
    : 'w-2 h-2 rounded-full bg-red-500';
}

function startPolling(page) {
  clearPollers();

  if (page === 'dashboard') {
    pollers.push(setInterval(() => pageHandlers.dashboard.refresh({ setBackendStatus }), POLL_INTERVAL_MS.estimate));
    pollers.push(setInterval(() => pageHandlers.dashboard.refreshMetrics({ setBackendStatus }), POLL_INTERVAL_MS.metrics));
  }

  if (page === 'analytics' || page === 'dashboard') {
    pollers.push(setInterval(() => pageHandlers.analytics.refresh({ setBackendStatus }), POLL_INTERVAL_MS.metrics));
  }

  if (page === 'calibration') {
    pollers.push(setInterval(() => pageHandlers.calibration.refresh(), POLL_INTERVAL_MS.health));
  }
}

function onRouteChange(page) {
  startPolling(page);
  if (pageHandlers[page] && typeof pageHandlers[page].mount === 'function') {
    pageHandlers[page].mount({ setBackendStatus });
  }
}

window.addEventListener('DOMContentLoaded', () => {
  initRouter({
    navLinks: elements.navLinks,
    pageSections: elements.pageSections,
    onRouteChange,
  });
});
