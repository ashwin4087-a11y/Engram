import { fetchJson } from '../api.js';
import { API_ROUTES } from '../config.js';

export async function runDiagnostics() {
  const result = await fetchJson(API_ROUTES.DIAGNOSTICS);
  return result;
}
