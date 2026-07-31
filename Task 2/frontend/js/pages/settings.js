const SETTINGS_KEY = 'optivue.settings';

function loadSavedSettings() {
  try {
    return JSON.parse(localStorage.getItem(SETTINGS_KEY) || '{}');
  } catch {
    return {};
  }
}

function populateInputs(values) {
  const cameraInput = document.getElementById('settings-camera');
  const thresholdInput = document.getElementById('settings-threshold');
  const themeInput = document.getElementById('settings-theme');

  if (cameraInput && values.cameraIndex != null) cameraInput.value = values.cameraIndex;
  if (thresholdInput && values.minConfidence != null) thresholdInput.value = values.minConfidence;
  if (themeInput && values.theme) themeInput.value = values.theme;
}

export const settings = {
  mount() {
    const status = document.getElementById('settings-status');
    const saveButton = document.getElementById('btn-save-settings');
    const saved = loadSavedSettings();

    populateInputs(saved);

    if (status) {
      status.textContent = saved.cameraIndex != null || saved.minConfidence != null
        ? `Saved settings: camera ${saved.cameraIndex ?? 0}, confidence ${saved.minConfidence ?? 0.5}`
        : 'Backend status: pending';
    }

    if (saveButton && !saveButton.dataset.bound) {
      saveButton.dataset.bound = 'true';
      saveButton.addEventListener('click', () => {
        const values = {
          cameraIndex: document.getElementById('settings-camera')?.value || '0',
          minConfidence: document.getElementById('settings-threshold')?.value || '0.5',
          theme: document.getElementById('settings-theme')?.value || 'Industrial Navy',
        };
        localStorage.setItem(SETTINGS_KEY, JSON.stringify(values));
        if (status) {
          status.textContent = `Saved settings: camera ${values.cameraIndex}, confidence ${values.minConfidence}`;
        }
      });
    }
  },
  refresh() {
    // Static settings content.
  },
};
