/**
 * Smart Waste Management System - API Client
 */

class ApiClient {
    constructor() {
        this.baseUrl = `${CONFIG.API_BASE_URL}/api/${CONFIG.API_VERSION}`;
    }
    
    /**
     * Get authentication token
     */
    getToken() {
        return localStorage.getItem('access_token') || sessionStorage.getItem('access_token');
    }
    
    /**
     * Make an API request
     */
    async request(endpoint, options = {}) {
        const url = `${this.baseUrl}${endpoint}`;
        
        const token = this.getToken();
        
        const defaultOptions = {
            headers: {
                'Content-Type': 'application/json',
            },
        };
        
        // Add auth token if available
        if (token) {
            defaultOptions.headers['Authorization'] = `Bearer ${token}`;
        }
        
        const response = await fetch(url, { ...defaultOptions, ...options });
        
        // Handle 401 Unauthorized
        if (response.status === 401) {
            // Clear tokens and redirect to login
            localStorage.removeItem('access_token');
            localStorage.removeItem('refresh_token');
            sessionStorage.removeItem('access_token');
            sessionStorage.removeItem('refresh_token');
            window.location.href = '/';
            return null;
        }
        
        if (!response.ok) {
            const error = await response.json().catch(() => ({}));
            throw new Error(error.detail || `HTTP ${response.status}: ${response.statusText}`);
        }
        
        // Return null for 204 No Content
        if (response.status === 204) {
            return null;
        }
        
        return response.json();
    }
    
    // ============== Dashboard ==============
    
    async getDashboardStats() {
        return this.request('/analytics/dashboard');
    }
    
    // ============== Bins ==============
    
    async getBins(params = {}) {
        const queryParams = new URLSearchParams(params).toString();
        const query = queryParams ? `?${queryParams}` : '';
        return this.request(`/bins/${query}`);
    }
    
    async getBin(binId, includeHistory = false) {
        return this.request(`/bins/${binId}?include_history=${includeHistory}`);
    }
    
    async createBin(binData) {
        return this.request('/bins/', {
            method: 'POST',
            body: JSON.stringify(binData)
        });
    }
    
    async updateBin(binId, binData) {
        return this.request(`/bins/${binId}`, {
            method: 'PUT',
            body: JSON.stringify(binData)
        });
    }
    
    async deleteBin(binId) {
        return this.request(`/bins/${binId}`, {
            method: 'DELETE'
        });
    }
    
    async collectBin(binId, notes = '') {
        return this.request(`/bins/${binId}/collect`, {
            method: 'POST',
            body: JSON.stringify({ notes })
        });
    }
    
    // ============== Sensor Readings ==============
    
    async getReadings(params = {}) {
        const queryParams = new URLSearchParams(params).toString();
        const query = queryParams ? `?${queryParams}` : '';
        return this.request(`/readings/${query}`);
    }
    
    async getLatestReadings() {
        return this.request('/readings/latest');
    }
    
    async createReading(readingData) {
        return this.request('/readings/', {
            method: 'POST',
            body: JSON.stringify(readingData)
        });
    }
    
    // ============== Analytics ==============
    
    async getFillPatterns(binId = null, days = 7) {
        const query = binId ? `?bin_id=${binId}&days=${days}` : `?days=${days}`;
        return this.request(`/analytics/fill-patterns${query}`);
    }
    
    async getPredictions(binId = null) {
        const query = binId ? `?bin_id=${binId}` : '';
        return this.request(`/analytics/predictions${query}`);
    }
    
    async getEfficiencyMetrics(days = 30) {
        return this.request(`/analytics/efficiency?days=${days}`);
    }
    
    async getZoneAnalysis() {
        return this.request('/analytics/zones');
    }
    
    async getHistoricalData(metric, days = 30) {
        return this.request(`/analytics/historical/${metric}?days=${days}`);
    }
    
    async getBinStatusDistribution() {
        return this.request('/analytics/bins/status-distribution');
    }
    
    async getFillTrends(days = 7) {
        return this.request(`/analytics/bins/fill-trends?days=${days}`);
    }
    
    // ============== Alerts ==============
    
    async getAlerts(params = {}) {
        const queryParams = new URLSearchParams(params).toString();
        const query = queryParams ? `?${queryParams}` : '';
        return this.request(`/alerts/${query}`);
    }
    
    async getUnresolvedAlerts(severity = null) {
        const query = severity ? `?severity=${severity}` : '';
        return this.request(`/alerts/unresolved${query}`);
    }
    
    async getCriticalAlertCount() {
        return this.request('/alerts/critical-count');
    }
    
    async resolveAlert(alertId, resolvedBy, notes = '') {
        return this.request(`/alerts/${alertId}/resolve`, {
            method: 'POST',
            body: JSON.stringify({ resolved_by: resolvedBy, resolution_notes: notes })
        });
    }
    
    async deleteAlert(alertId) {
        return this.request(`/alerts/${alertId}`, {
            method: 'DELETE'
        });
    }
    
    async getAlertStatistics(days = 30) {
        return this.request(`/alerts/stats/summary?days=${days}`);
    }
    
    async checkOfflineSensors(thresholdMinutes = 120) {
        return this.request(`/alerts/check/offline-sensors?threshold_minutes=${thresholdMinutes}`);
    }
    
    // ============== Routes ==============
    
    async getRoutes(params = {}) {
        const queryParams = new URLSearchParams(params).toString();
        const query = queryParams ? `?${queryParams}` : '';
        return this.request(`/routes/${query}`);
    }
    
    async getRoute(routeId) {
        return this.request(`/routes/${routeId}`);
    }
    
    async getRouteStops(routeId) {
        return this.request(`/routes/${routeId}/stops`);
    }
    
    async createRoute(routeData) {
        return this.request('/routes/', {
            method: 'POST',
            body: JSON.stringify(routeData)
        });
    }
    
    async updateRoute(routeId, routeData) {
        return this.request(`/routes/${routeId}`, {
            method: 'PUT',
            body: JSON.stringify(routeData)
        });
    }
    
    async deleteRoute(routeId) {
        return this.request(`/routes/${routeId}`, {
            method: 'DELETE'
        });
    }
    
    async optimizeRoute(binIds, startLocation = null, vehicleCapacity = 5000) {
        return this.request('/routes/optimize', {
            method: 'POST',
            body: JSON.stringify({
                bin_ids: binIds,
                start_location: startLocation,
                vehicle_capacity: vehicleCapacity
            })
        });
    }
    
    async generateSmartRoute(zone = null, maxBins = 15, minFillLevel = 60) {
        const params = new URLSearchParams();
        if (zone) params.append('zone', zone);
        params.append('max_bins', maxBins);
        params.append('min_fill_level', minFillLevel);
        
        return this.request(`/routes/generate-smart?${params.toString()}`, {
            method: 'POST'
        });
    }
    
    async startRoute(routeId) {
        return this.request(`/routes/${routeId}/start`, {
            method: 'POST'
        });
    }
    
    async completeRoute(routeId) {
        return this.request(`/routes/${routeId}/complete`, {
            method: 'POST'
        });
    }
    
    async getRouteStatistics(days = 30) {
        return this.request(`/routes/stats/summary?days=${days}`);
    }
    
    // ============== Seed Data ==============
    
    async seedData() {
        return this.request('/seed-data', {
            method: 'POST'
        });
    }
}

// Create global API client instance
const api = new ApiClient();
