/**
 * Smart Waste Management System - Map Manager
 */

class MapManager {
    constructor() {
        this.map = null;
        this.markers = {};
        this.binData = {};
    }
    
    /**
     * Initialize the map
     */
    initMap(containerId) {
        if (this.map) {
            return;
        }
        
        this.map = L.map(containerId).setView(
            CONFIG.MAP_DEFAULT_CENTER, 
            CONFIG.MAP_DEFAULT_ZOOM
        );
        
        // Add tile layer
        L.tileLayer(CONFIG.MAP_TILE_URL, {
            attribution: '&copy; <a href="https://openstreetmap.org">OpenStreetMap</a> contributors',
            maxZoom: 19
        }).addTo(this.map);
        
        return this.map;
    }
    
    /**
     * Get marker color based on fill level
     */
    getMarkerColor(fillLevel) {
        if (fillLevel >= CONFIG.FILL_THRESHOLDS.HIGH) {
            return CONFIG.CHART_COLORS.critical;
        } else if (fillLevel >= CONFIG.FILL_THRESHOLDS.MEDIUM) {
            return CONFIG.CHART_COLORS.danger;
        } else if (fillLevel >= CONFIG.FILL_THRESHOLDS.LOW) {
            return CONFIG.CHART_COLORS.warning;
        }
        return CONFIG.CHART_COLORS.success;
    }
    
    /**
     * Create custom marker icon
     */
    createMarkerIcon(fillLevel) {
        const color = this.getMarkerColor(fillLevel);
        
        return L.divIcon({
            className: 'custom-marker',
            html: `
                <div style="
                    width: 30px;
                    height: 30px;
                    background: ${color};
                    border: 3px solid white;
                    border-radius: 50%;
                    box-shadow: 0 2px 6px rgba(0,0,0,0.3);
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    color: white;
                    font-size: 12px;
                    font-weight: bold;
                ">
                    <i class="fas fa-trash" style="font-size: 10px;"></i>
                </div>
            `,
            iconSize: [30, 30],
            iconAnchor: [15, 15]
        });
    }
    
    /**
     * Add or update a bin marker
     */
    updateBinMarker(bin) {
        const binId = bin.id;
        const lat = bin.latitude;
        const lon = bin.longitude;
        const fillLevel = bin.latest_reading ? bin.latest_reading.fill_level_percent : 0;
        
        // Remove existing marker if present
        if (this.markers[binId]) {
            this.map.removeLayer(this.markers[binId]);
        }
        
        // Create marker
        const marker = L.marker([lat, lon], {
            icon: this.createMarkerIcon(fillLevel)
        }).addTo(this.map);
        
        // Create popup content
        const popupContent = `
            <div style="min-width: 200px;">
                <h4 style="margin: 0 0 8px 0; font-size: 14px;">${bin.location_name}</h4>
                <div style="margin-bottom: 8px;">
                    <span style="font-size: 12px; color: #666;">Type:</span>
                    <span style="font-size: 12px; text-transform: capitalize;">${bin.bin_type}</span>
                </div>
                <div style="margin-bottom: 8px;">
                    <span style="font-size: 12px; color: #666;">Fill Level:</span>
                    <span style="font-size: 14px; font-weight: bold; color: ${this.getMarkerColor(fillLevel)};">
                        ${fillLevel.toFixed(1)}%
                    </span>
                </div>
                <div style="margin-bottom: 8px;">
                    <span style="font-size: 12px; color: #666;">Capacity:</span>
                    <span style="font-size: 12px;">${bin.capacity_liters} L</span>
                </div>
                ${bin.latest_reading ? `
                    <div style="font-size: 11px; color: #999; margin-top: 8px;">
                        Last updated: ${new Date(bin.latest_reading.timestamp).toLocaleString()}
                    </div>
                ` : ''}
                <div style="margin-top: 12px; text-align: center;">
                    <button onclick="app.collectBin(${binId})" 
                            style="background: #10B981; color: white; border: none; padding: 6px 12px; 
                                   border-radius: 4px; font-size: 12px; cursor: pointer;">
                        Mark Collected
                    </button>
                </div>
            </div>
        `;
        
        marker.bindPopup(popupContent);
        
        this.markers[binId] = marker;
        this.binData[binId] = bin;
    }
    
    /**
     * Update multiple bin markers
     */
    updateBinMarkers(bins) {
        bins.forEach(bin => this.updateBinMarker(bin));
        
        // Fit bounds if we have markers
        const markerValues = Object.values(this.markers);
        if (markerValues.length > 0) {
            const group = new L.featureGroup(markerValues);
            this.map.fitBounds(group.getBounds().pad(0.1));
        }
    }
    
    /**
     * Remove a bin marker
     */
    removeBinMarker(binId) {
        if (this.markers[binId]) {
            this.map.removeLayer(this.markers[binId]);
            delete this.markers[binId];
            delete this.binData[binId];
        }
    }
    
    /**
     * Clear all markers
     */
    clearMarkers() {
        Object.values(this.markers).forEach(marker => {
            this.map.removeLayer(marker);
        });
        this.markers = {};
        this.binData = {};
    }
    
    /**
     * Draw a route on the map
     */
    drawRoute(waypoints, options = {}) {
        // Remove existing route if any
        if (this.routeLine) {
            this.map.removeLayer(this.routeLine);
        }
        if (this.routeMarkers) {
            this.routeMarkers.forEach(m => this.map.removeLayer(m));
        }
        
        if (!waypoints || waypoints.length < 2) {
            return;
        }
        
        this.routeMarkers = [];
        
        // Add numbered markers for each waypoint
        waypoints.forEach((wp, index) => {
            const marker = L.marker([wp.coordinates[0], wp.coordinates[1]], {
                icon: L.divIcon({
                    className: 'route-marker',
                    html: `
                        <div style="
                            width: 24px;
                            height: 24px;
                            background: #3B82F6;
                            border: 2px solid white;
                            border-radius: 50%;
                            box-shadow: 0 2px 4px rgba(0,0,0,0.3);
                            display: flex;
                            align-items: center;
                            justify-content: center;
                            color: white;
                            font-size: 11px;
                            font-weight: bold;
                        ">${index + 1}</div>
                    `,
                    iconSize: [24, 24],
                    iconAnchor: [12, 12]
                })
            }).addTo(this.map);
            
            marker.bindPopup(`
                <div>
                    <strong>Stop ${index + 1}</strong><br>
                    ${wp.location}<br>
                    Fill: ${wp.fill_level}%
                </div>
            `);
            
            this.routeMarkers.push(marker);
        });
        
        // Draw route line
        const latLngs = waypoints.map(wp => [wp.coordinates[0], wp.coordinates[1]]);
        this.routeLine = L.polyline(latLngs, {
            color: '#3B82F6',
            weight: 4,
            opacity: 0.8,
            dashArray: '10, 10'
        }).addTo(this.map);
        
        // Fit bounds
        this.map.fitBounds(this.routeLine.getBounds().pad(0.1));
    }
    
    /**
     * Clear route from map
     */
    clearRoute() {
        if (this.routeLine) {
            this.map.removeLayer(this.routeLine);
            this.routeLine = null;
        }
        if (this.routeMarkers) {
            this.routeMarkers.forEach(m => this.map.removeLayer(m));
            this.routeMarkers = [];
        }
    }
    
    /**
     * Resize map (call when container size changes)
     */
    resize() {
        if (this.map) {
            this.map.invalidateSize();
        }
    }
}

// Create global map manager instance
const mapManager = new MapManager();
