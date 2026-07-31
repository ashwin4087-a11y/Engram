import { fetchJson } from '../api.js';
import { API_ROUTES } from '../config.js';

export async function fetchMetrics() {
  const result = await fetchJson(API_ROUTES.METRICS);
  if (!result || !result.success || !result.data) return null;
  return {
    fps: result.data.fps,
    uptimeSeconds: result.data.uptime_seconds,
    calibration: result.data.calibration,
    camera: result.data.camera,
    healthStatus: result.data.status,
    totalLatency: result.data.total_pipeline_latency_ms,
    raw: result.data,
  };
}
