import { fetchEstimate, fetchMetrics, captureFrame } from '../services/index.js';

const elements = {
  distance: () => document.getElementById('val-distance'),
  angle: () => document.getElementById('val-angle'),
  confidence: () => document.getElementById('val-confidence'),
  fps: () => document.getElementById('val-fps'),
  liveStream: () => document.getElementById('live-stream'),
};

function updateEstimateData(data) {
  const distance = elements.distance();
  const angle = elements.angle();
  const confidence = elements.confidence();

  if (distance && data.estimate && data.estimate.distance != null) {
    distance.innerHTML = `${(data.estimate.distance * 1000).toFixed(0)} <span class="text-lg">mm</span>`;
  }
  if (angle && data.estimate && data.estimate.angle != null) {
    angle.innerHTML = `${data.estimate.angle.toFixed(1)}° <span class="text-primary-fixed">Δ</span>`;
  }
  if (confidence && data.estimate && data.estimate.confidence != null) {
    confidence.innerText = `${(data.estimate.confidence * 100).toFixed(1)}%`;
  }
}

function updateMetricsData(data) {
  const fps = elements.fps();
  if (fps && data.fps != null) {
    fps.innerText = data.fps.toFixed(1);
  }
}

export const dashboard = {
  async mount({ setBackendStatus }) {
    this.setBackendStatus = setBackendStatus;
    await this.refresh({ setBackendStatus });
    await this.refreshMetrics({ setBackendStatus });
    this.attachControls();
    this.renderSessionHistory();
  },

  attachControls() {
    const btnCapture = document.getElementById('btn-capture-frame');
    const btnFull = document.getElementById('btn-fullscreen');
    const live = elements.liveStream();

    if (!this.controlsAttached) {
      if (btnCapture) {
        btnCapture.disabled = false;
        btnCapture.classList.remove('pointer-events-none', 'opacity-60');
        btnCapture.addEventListener('click', async () => {
          await this.handleCapture();
        });
      }

      if (btnFull && live) {
        btnFull.disabled = false;
        btnFull.classList.remove('pointer-events-none', 'opacity-60');
        btnFull.addEventListener('click', async () => {
          try {
            const viewport = document.getElementById('camera-viewport');
            if (!document.fullscreenElement) {
              await viewport?.requestFullscreen();
            } else {
              await document.exitFullscreen();
            }
          } catch (err) {
            console.error('Fullscreen error', err);
          }
        });
      }

      this.controlsAttached = true;
    }
  },

  async handleCapture() {
    const live = elements.liveStream();
    if (!live) return;
    try {
      const canvas = document.createElement('canvas');
      const context = canvas.getContext('2d');
      const width = live.naturalWidth || 640;
      const height = live.naturalHeight || 480;

      canvas.width = width;
      canvas.height = height;

      context.drawImage(live, 0, 0, width, height);
      const blob = await new Promise((resolve, reject) => {
        canvas.toBlob((value) => {
          if (value) resolve(value);
          else reject(new Error('Unable to create capture blob'));
        }, 'image/jpeg', 0.92);
      });

      const dataUrl = await new Promise((resolve) => {
        const reader = new FileReader();
        reader.onload = () => resolve(reader.result);
        reader.readAsDataURL(blob);
      });

      const getText = (el) => (el ? el.innerText.trim() : '');
      const metadata = {
        timestamp: new Date().toISOString(),
        distance: getText(elements.distance()),
        angle: getText(elements.angle()),
        confidence: getText(elements.confidence()),
        fps: getText(elements.fps()),
      };

      const form = new FormData();
      const fileName = `capture-${Date.now()}.jpg`;
      form.append('file', blob, fileName);
      form.append('metadata', JSON.stringify(metadata));

      const entry = { id: `s-${Date.now()}`, image: dataUrl, metadata };
      this.addToLocalHistory(entry);
      this.showToast('Capture saved locally');

      const result = await captureFrame(form);
      if (result && result.success) {
        try {
          const serverId = result.capture_id || result.captureId || null;
          const path = result.path || result.url || null;
          const key = 'optivue.session.history';
          const current = JSON.parse(localStorage.getItem(key) || '[]');
          const ts = metadata.timestamp;
          for (let i = 0; i < current.length; i += 1) {
            if (current[i].metadata && current[i].metadata.timestamp === ts) {
              current[i].server = { id: serverId, path };
              break;
            }
          }
          localStorage.setItem(key, JSON.stringify(current));
        } catch (e) {
          console.warn('update local entry failed', e);
        }
        this.showToast('Capture uploaded');
      } else {
        this.showToast('Upload failed — saved locally');
      }
      this.renderSessionHistory();
    } catch (err) {
      console.error('capture failed', err);
      this.showToast('Capture failed');
    }
  },

  addToLocalHistory(entry) {
    try {
      const key = 'optivue.session.history';
      const current = JSON.parse(localStorage.getItem(key) || '[]');
      current.unshift(entry);
      // keep max 50
      localStorage.setItem(key, JSON.stringify(current.slice(0,50)));
    } catch (err) {
      console.error('store history', err);
    }
  },

  getLocalHistory() {
    try {
      const key = 'optivue.session.history';
      return JSON.parse(localStorage.getItem(key) || '[]');
    } catch (err) {
      return [];
    }
  },

  renderSessionHistory() {
    const list = document.getElementById('session-history-list');
    if (!list) return;
    const items = this.getLocalHistory();
    list.innerHTML = '';
    if (!items.length) {
      list.innerHTML = '<p class="text-on-surface-variant">No captures yet.</p>';
      return;
    }
    items.slice(0,8).forEach(it => {
      const div = document.createElement('div');
      div.className = 'flex items-center gap-sm p-sm bg-surface rounded-lg border border-outline-variant';
      div.innerHTML = `
        <img src="${it.image}" alt="capture" class="w-16 h-12 object-cover rounded" />
        <div class="flex-1">
          <div class="font-label-sm text-on-surface">${new Date(it.metadata.timestamp).toLocaleString()}</div>
          <div class="text-on-surface-variant text-sm">${it.metadata.distance} • ${it.metadata.confidence}</div>
        </div>
        <button class="button-secondary" data-id="${it.id}">Details</button>
      `;
      list.appendChild(div);
    });
  },

  showToast(msg, timeout = 2500) {
    const el = document.createElement('div');
    el.className = 'fixed bottom-6 right-6 bg-primary-700 text-white px-4 py-2 rounded shadow-lg';
    el.innerText = msg;
    document.body.appendChild(el);
    setTimeout(() => el.remove(), timeout);
  },

  async refresh({ setBackendStatus }) {
    const result = await fetchEstimate();
    if (!result || typeof result !== 'object') {
      setBackendStatus(false);
      return;
    }
    setBackendStatus(true);
    updateEstimateData(result);
  },

  async refreshMetrics({ setBackendStatus }) {
    const result = await fetchMetrics();
    if (!result || typeof result !== 'object') {
      setBackendStatus(false);
      return;
    }
    setBackendStatus(true);
    updateMetricsData(result);
  },
};
