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
  async mount() {
    await this.refresh();
    this.renderCaptures();
  },

  async refresh({ setBackendStatus }) {
    const result = await fetchMetrics();
    if (!result) {
      if (setBackendStatus) setBackendStatus(false);
      return;
    }
    if (setBackendStatus) setBackendStatus(true);
    if (!result.success || !result.data) return;
    const data = result.data;
    const fpsElement = elements.fps();
    if (fpsElement) fpsElement.innerText = data.fps != null ? data.fps.toFixed(1) : '--';
    const cameraElement = elements.camera();
    if (cameraElement) cameraElement.innerText = data.camera ?? '--';
    const calibrationElement = elements.calibration();
    if (calibrationElement) calibrationElement.innerText = data.calibration ?? '--';
    const totalLatency = data.total_pipeline_latency_ms ?? (data.camera_latency_ms + data.detection_latency_ms + data.estimation_latency_ms);
    const latencyElement = elements.latency();
    if (latencyElement) latencyElement.innerText = totalLatency != null ? totalLatency.toFixed(1) : '--';
    const healthText = data.status === 'ERROR' || data.status === 'NO_CAMERA' ? data.status : 'OPERATIONAL';
    const statusElement = elements.status();
    if (statusElement) statusElement.innerText = healthText;
    const uptimeElement = elements.uptime();
    if (uptimeElement) uptimeElement.innerText = formatUptime(data.uptime_seconds);
  },

  async renderCaptures() {
    const container = document.getElementById('analytics-captures');
    if (!container) return;
    const result = await fetchCaptures();
    if (!result || !result.success) {
      container.innerHTML = '<p class="text-on-surface-variant">No captures available.</p>';
      return;
    }
    const items = result.data || [];
    if (!items.length) {
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
