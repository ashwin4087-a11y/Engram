export const API_BASE_URL = '';

export const API_ROUTES = {
  ESTIMATE: '/estimate',
  METRICS: '/metrics',
  HEALTH: '/health',
  CALIBRATION: '/calibration',
  CALIBRATE: '/calibrate',
  DIAGNOSTICS: '/diagnostics',
  PREVIEW: '/preview',
  CAPTURE: '/capture',
};

export const APP_ROUTES = ['dashboard', 'calibration', 'analytics', 'evaluation', 'architecture', 'demoGuide', 'settings', 'about'];
export const DEFAULT_ROUTE = 'dashboard';

export const POLL_INTERVAL_MS = {
  estimate: 1000,
  metrics: 1000,
  health: 5000,
};

export const REQUEST_TIMEOUT_MS = 10000;
export const PREVIEW_MODE = 'default';

export const FEATURE_FLAGS = {
  diagnostics: false,
  captureFrame: true,
  fullscreen: true,
};
