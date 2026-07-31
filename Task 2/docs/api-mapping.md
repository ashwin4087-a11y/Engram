# API Mapping

| Endpoint | HTTP Method | Frontend Service | Page/Component | Purpose |
|---|---|---|---|---|
| `/estimate` | GET | `./frontend/js/services/estimateService.js` | `dashboard.js` | Fetch live distance, angle, confidence metrics. |
| `/metrics` | GET | `./frontend/js/services/metricsService.js` | `dashboard.js`, `analytics.js` | Fetch pipeline performance and health report. |
| `/health` | GET | `./frontend/js/services/healthService.js` | `dashboard.js`, `analytics.js` | Fetch API and backend connection health. |
| `/calibration` | GET | `./frontend/js/services/calibrationService.js` | `calibration.js` | Fetch current calibration status. |
| `/calibrate` | POST | `./frontend/js/services/calibrationService.js` | `calibration.js` | Submit calibration parameters and trigger backend calibration. |
| `/preview` | GET | `./frontend/js/services/previewService.js` | `dashboard.js` (image source) | Build live MJPEG preview stream URL. |
| `/diagnostics` | GET | `./frontend/js/services/diagnosticsService.js` | Future diagnostics UI | Placeholder diagnostics endpoint call. |
