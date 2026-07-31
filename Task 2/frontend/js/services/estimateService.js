import { fetchJson } from '../api.js';
import { API_ROUTES } from '../config.js';
import { formatDistanceMeters, formatPercentage } from '../utils/formatters.js';

export async function fetchEstimate() {
  const result = await fetchJson(API_ROUTES.ESTIMATE);
  if (!result || !result.success || !result.data) return null;
  const estimate = result.data.estimate;
  return {
    distance: estimate?.distance != null ? formatDistanceMeters(estimate.distance) : '--',
    confidence: estimate?.confidence != null ? formatPercentage(estimate.confidence) : '--%',
    angle: estimate?.angle != null ? `${estimate.angle.toFixed(1)}°` : '--°',
    raw: estimate,
  };
}
