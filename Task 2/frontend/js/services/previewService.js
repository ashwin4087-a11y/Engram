import { API_BASE_URL, API_ROUTES, PREVIEW_MODE } from '../config.js';

export function previewUrl(mode = PREVIEW_MODE) {
  return `${API_BASE_URL}${API_ROUTES.PREVIEW}?mode=${mode}`;
}
