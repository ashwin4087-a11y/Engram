export function formatDistanceMeters(value) {
  if (value == null || Number.isNaN(value)) return '--';
  return `${(value * 1000).toFixed(0)} mm`;
}

export function formatPercentage(value) {
  if (value == null || Number.isNaN(value)) return '--%';
  return `${(value * 100).toFixed(1)}%`;
}

export function formatUptime(seconds) {
  if (seconds == null || Number.isNaN(seconds)) return '00:00:00';
  const h = Math.floor(seconds / 3600);
  const m = Math.floor((seconds % 3600) / 60);
  const s = Math.floor(seconds % 60);
  return [h, m, s].map(v => v.toString().padStart(2, '0')).join(':');
}
