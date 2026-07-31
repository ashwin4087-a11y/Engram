import { fetchJson } from '../api.js';
import { API_ROUTES } from '../config.js';

export async function fetchHealth() {
  const result = await fetchJson(API_ROUTES.HEALTH);
  if (!result || !result.success || !result.data) return null;
  return {
    status: result.data.status,
    raw: result.data,
  };
}
