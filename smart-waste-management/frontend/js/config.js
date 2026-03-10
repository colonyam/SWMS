/**
 * Smart Waste Management System - Configuration
 */

const CONFIG = {
    // API Configuration
    API_BASE_URL: window.location.hostname === 'localhost' 
        ? 'http://localhost:8000' 
        : '',
    API_VERSION: 'v1',
    
    // WebSocket Configuration
    WS_URL: window.location.hostname === 'localhost'
        ? 'ws://localhost:8000/ws'
        : `ws://${window.location.host}/ws`,
    WS_RECONNECT_INTERVAL: 3000,
    WS_MAX_RECONNECT_ATTEMPTS: 10,
    
    // Refresh Intervals (milliseconds)
    DASHBOARD_REFRESH_INTERVAL: 30000,
    BINS_REFRESH_INTERVAL: 60000,
    ALERTS_REFRESH_INTERVAL: 15000,
    MAP_REFRESH_INTERVAL: 30000,
    
    // Chart Colors
    CHART_COLORS: {
        primary: '#10B981',
        secondary: '#3B82F6',
        accent: '#F59E0B',
        success: '#22C55E',
        warning: '#EAB308',
        danger: '#EF4444',
        critical: '#DC2626',
        gray: '#94A3B8',
        lightGray: '#E2E8F0'
    },
    
    // Fill Level Thresholds
    FILL_THRESHOLDS: {
        LOW: 50,
        MEDIUM: 80,
        HIGH: 95
    },
    
    // Map Configuration
    MAP_DEFAULT_CENTER: [40.7484, -73.9857], // NYC
    MAP_DEFAULT_ZOOM: 12,
    MAP_TILE_URL: 'https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png',
    
    // Pagination
    DEFAULT_PAGE_SIZE: 20,
    
    // Date Formats
    DATE_FORMAT: 'YYYY-MM-DD HH:mm:ss',
    SHORT_DATE_FORMAT: 'MMM DD, HH:mm'
};

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = CONFIG;
}
