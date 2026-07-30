/**
 * api.js - Handles communication with the FastAPI Backend
 */

const API_BASE_URL = 'http://127.0.0.1:8000';

class BackendAPI {
    /**
     * Fetches the latest tracker estimation state.
     */
    static async getEstimate() {
        try {
            const response = await fetch(`${API_BASE_URL}/estimate`);
            if (!response.ok) throw new Error('Network response was not ok');
            return await response.json();
        } catch (error) {
            console.error("Failed to fetch estimate:", error);
            return null;
        }
    }

    /**
     * Fetches system metrics and performance data.
     */
    static async getMetrics() {
        try {
            const response = await fetch(`${API_BASE_URL}/metrics`);
            if (!response.ok) throw new Error('Network response was not ok');
            return await response.json();
        } catch (error) {
            console.error("Failed to fetch metrics:", error);
            return null;
        }
    }
}
