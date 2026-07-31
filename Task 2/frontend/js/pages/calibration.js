import { fetchCalibration, runCalibration } from '../services/index.js';

const elements = {
  statusText: () => document.getElementById('calibration-page-status-text'),
  timestamp: () => document.getElementById('calibration-page-timestamp'),
  button: () => document.getElementById('btn-run-calibration'),
  distanceInput: () => document.getElementById('calib-distance'),
  widthInput: () => document.getElementById('calib-width'),
  message: () => document.getElementById('calibration-message'),
};

async function refreshCalibration() {
  const result = await fetchCalibration();
  const statusText = elements.statusText();
  const timestamp = elements.timestamp();

  if (!statusText || !timestamp) return;
  if (!result) {
    statusText.innerText = 'Offline';
    timestamp.innerText = '--';
    return;
  }

  const calibrated = result.success && result.data && result.data.calibrated;
  statusText.innerText = calibrated ? 'Calibrated' : 'Not calibrated';
  timestamp.innerText = new Date().toLocaleString();
}

export const calibration = {
  mount() {
    const button = elements.button();
    if (!button) return;
    button.addEventListener('click', async event => {
      event.preventDefault();
      const knownDistance = parseFloat(elements.distanceInput()?.value || '0');
      const knownWidth = parseFloat(elements.widthInput()?.value || '0');
      const message = elements.message();
      if (message) {
        message.innerText = 'Running calibration...';
      }
      const result = await runCalibration(knownDistance, knownWidth);
      if (message) {
        if (result && result.success) {
          message.innerText = 'Calibration successful.';
        } else {
          message.innerText = 'Calibration failed. Check backend status.';
        }
      }
      await refreshCalibration();
    });
  },

  async refresh() {
    await refreshCalibration();
  },
};
