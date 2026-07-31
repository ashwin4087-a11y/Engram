import { fetchJson } from '../api.js';
import { API_ROUTES } from '../config.js';

export async function fetchCalibration() {
  const result = await fetchJson(API_ROUTES.CALIBRATION);
  if (!result || !result.success || !result.data) return null;
  return {
    calibrated: result.data.calibrated,
    raw: result.data,
  };
}

export async function runCalibration(knownDistance, knownFaceWidth) {
  const result = await fetchJson(API_ROUTES.CALIBRATE, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ known_distance: knownDistance, known_face_width: knownFaceWidth }),
  });
  return result;
}
