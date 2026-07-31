import { BackendAPI } from '../api.js';

export async function fetchEstimate() {
  return BackendAPI.getEstimate();
}

export async function fetchMetrics() {
  return BackendAPI.getMetrics();
}

export async function fetchHealth() {
  return BackendAPI.getHealth();
}

export async function fetchCalibration() {
  return BackendAPI.getCalibration();
}

export async function runCalibration(knownDistance, knownFaceWidth) {
  return BackendAPI.runCalibration(knownDistance, knownFaceWidth);
}

export async function captureFrame(formData) {
  return BackendAPI.captureFrame(formData);
}

export async function fetchCaptures() {
  return BackendAPI.fetchCaptures();
}
