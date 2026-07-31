import { API_BASE_URL, API_ROUTES } from './config.js';

function buildUrl(path) {
  return `${API_BASE_URL}${path}`;
}

function unwrapApiPayload(payload) {
  if (!payload || typeof payload !== 'object') {
    return payload;
  }

  if (Object.prototype.hasOwnProperty.call(payload, 'success') && Object.prototype.hasOwnProperty.call(payload, 'data')) {
    if (!payload.success) {
      return null;
    }
    return payload.data ?? payload;
  }

  return payload;
}

export async function fetchJson(path, options = {}) {
  try {
    const url = buildUrl(path);
    const response = await fetch(url, options);
    if (!response.ok) {
      throw new Error(`Request failed ${response.status} ${response.statusText}`);
    }
    const payload = await response.json();
    return unwrapApiPayload(payload);
  } catch (error) {
    console.error(`API fetch error for ${path}:`, error);
    return null;
  }
}

export const BackendAPI = {
  getEstimate: () => fetchJson(API_ROUTES.ESTIMATE),
  getMetrics: () => fetchJson(API_ROUTES.METRICS),
  getHealth: () => fetchJson(API_ROUTES.HEALTH),
  getCalibration: () => fetchJson(API_ROUTES.CALIBRATION),
  runCalibration: (knownDistance, knownFaceWidth) =>
    fetchJson(API_ROUTES.CALIBRATE, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ known_distance: knownDistance, known_face_width: knownFaceWidth }),
    }),
  captureFrame: (formData) => {
    // POST multipart/form-data to capture endpoint
    try {
      const url = buildUrl(API_ROUTES.CAPTURE);
      return fetch(url, { method: 'POST', body: formData }).then(async res => {
        if (!res.ok) throw new Error('Capture failed');
        return await res.json();
      }).catch(err => {
        console.error('Capture API error', err);
        return null;
      });
    } catch (err) {
      console.error('captureFrame error', err);
      return null;
    }
  },
  fetchCaptures: () => fetchJson('/captures'),
};
