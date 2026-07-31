import { fetchMetrics, fetchCaptures } from '../services/index.js';

const elements = {
  fps: () => document.getElementById('analytics-fps'),
  camera: () => document.getElementById('analytics-camera'),
  calibration: () => document.getElementById('analytics-calibration'),
  latency: () => document.getElementById('analytics-latency'),
  status: () => document.getElementById('analytics-status'),
  uptime: () => document.getElementById('analytics-uptime'),
};

function formatUptime(seconds) {
  if (!seconds) return '00:00:00';
  const h = Math.floor(seconds / 3600);
  const m = Math.floor((seconds % 3600) / 60);
  const s = Math.floor(seconds % 60);
  return [h, m, s].map(v => v.toString().padStart(2, '0')).join(':');
}

export const analytics = {
  async mount(options = {}) {
    await this.refresh(options);
    this.renderCaptures();
  },

  async refresh(options = {}) {
    const { setBackendStatus } = options || {};
    const result = await fetchMetrics();
    if (!result || typeof result !== 'object') {
      if (setBackendStatus) setBackendStatus(false);
      return;
    }
    if (setBackendStatus) setBackendStatus(true);

    const data = result;
    const fpsElement = elements.fps();
    if (fpsElement) fpsElement.innerText = data.fps != null ? data.fps.toFixed(1) : '--';
    const cameraElement = elements.camera();
    if (cameraElement) cameraElement.innerText = data.camera ?? '--';
    const calibrationElement = elements.calibration();
    if (calibrationElement) calibrationElement.innerText = data.calibration ?? '--';
    const totalLatency = data.total_pipeline_latency_ms ?? (
      (data.camera_latency_ms ?? 0) + (data.detection_latency_ms ?? 0) + (data.estimation_latency_ms ?? 0)
    );
    const latencyElement = elements.latency();
    if (latencyElement) latencyElement.innerText = totalLatency != null ? totalLatency.toFixed(1) : '--';
    const healthText = data.status === 'ERROR' || data.status === 'NO_CAMERA' ? data.status : 'OPERATIONAL';
    const statusElement = elements.status();
    if (statusElement) statusElement.innerText = healthText;
    const uptimeElement = elements.uptime();
    if (uptimeElement) uptimeElement.innerText = formatUptime(data.uptime_seconds ?? data.uptimeSeconds);
  },

  async renderCaptures() {
    const container = document.getElementById('analytics-captures');
    if (!container) return;
    const items = await fetchCaptures();
    if (!Array.isArray(items) || !items.length) {
      container.innerHTML = '<p class="text-on-surface-variant">No captures available.</p>';
      return;
    }
    container.innerHTML = '';
    items.slice(0,6).forEach(it => {
      const img = document.createElement('img');
      img.src = '/captures/' + it.filename;
      img.alt = it.id;
      img.className = 'w-full h-24 object-cover rounded';
      container.appendChild(img);
    });
  }
};
