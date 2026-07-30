/**
 * dashboard.js - Main frontend logic for updating the UI
 */

document.addEventListener('DOMContentLoaded', () => {
    
    // DOM Elements
    const elements = {
        distance: document.getElementById('val-distance'),
        angle: document.getElementById('val-angle'),
        confidence: document.getElementById('val-confidence'),
        fps: document.getElementById('val-fps'),
        uptime: document.getElementById('val-uptime'),
        calStatus: document.getElementById('val-calibration-status'),
        calTime: document.getElementById('val-calibration-time'),
        sysHealth: document.getElementById('val-system-health')
    };

    /**
     * Formats seconds into HH:MM:SS
     */
    function formatUptime(seconds) {
        if (!seconds) return "00:00:00";
        const h = Math.floor(seconds / 3600);
        const m = Math.floor((seconds % 3600) / 60);
        const s = Math.floor(seconds % 60);
        return [h, m, s].map(v => v.toString().padStart(2, '0')).join(':');
    }

    /**
     * Poll the /estimate endpoint
     */
    async function updateEstimate() {
        const result = await BackendAPI.getEstimate();
        if (result && result.success && result.data) {
            const data = result.data;
            
            // Distance (convert m to mm for UI)
            if (data.estimate && data.estimate.distance) {
                const distMm = (data.estimate.distance * 1000).toFixed(0);
                elements.distance.innerHTML = `${distMm} <span class="text-lg">mm</span>`;
            } else {
                elements.distance.innerHTML = `-- <span class="text-lg">mm</span>`;
            }

            // Angle
            if (data.estimate && data.estimate.angle !== undefined) {
                elements.angle.innerHTML = `${data.estimate.angle.toFixed(1)}° <span class="text-primary-fixed">Δ</span>`;
            } else {
                elements.angle.innerHTML = `--° <span class="text-primary-fixed">Δ</span>`;
            }

            // Confidence
            if (data.estimate && data.estimate.confidence !== undefined) {
                elements.confidence.innerText = `${(data.estimate.confidence * 100).toFixed(1)}%`;
            } else {
                elements.confidence.innerText = `--%`;
            }

            // Optional: You could update FPS here too, but /metrics is better for rolling average
        }
    }

    /**
     * Poll the /metrics endpoint
     */
    async function updateMetrics() {
        const result = await BackendAPI.getMetrics();
        if (result && result.success && result.data) {
            const data = result.data;
            
            elements.fps.innerText = data.fps.toFixed(1);
            elements.uptime.innerText = formatUptime(data.uptime_seconds);
            
            elements.calStatus.innerText = data.calibration;
            if (data.calibration === "READY") {
                elements.calStatus.classList.remove('text-error');
                elements.calStatus.classList.add('text-primary');
                elements.calTime.innerText = "System calibrated";
            } else {
                elements.calStatus.classList.add('text-error');
                elements.calStatus.classList.remove('text-primary');
                elements.calTime.innerText = "Needs calibration";
            }

            if (data.status === "ERROR" || data.status === "NO_CAMERA") {
                elements.sysHealth.innerText = data.status;
                elements.sysHealth.parentElement.classList.replace('bg-emerald-100', 'bg-error-container');
                elements.sysHealth.parentElement.classList.replace('text-emerald-800', 'text-error');
            } else {
                elements.sysHealth.innerText = "OPERATIONAL";
                elements.sysHealth.parentElement.classList.replace('bg-error-container', 'bg-emerald-100');
                elements.sysHealth.parentElement.classList.replace('text-error', 'text-emerald-800');
            }
        }
    }

    // Start polling loops
    setInterval(updateEstimate, 100); // 10Hz updates for real-time feel on HUD
    setInterval(updateMetrics, 1000); // 1Hz updates for system metrics
});
