/**
 * Smart Waste Management System - Main Application
 */

class SmartWasteApp {
    constructor() {
        this.currentPage = 'dashboard';
        this.ws = null;
        this.wsReconnectAttempts = 0;
        this.refreshIntervals = {};
        this.bins = [];
        this.alerts = [];
        this.currentUser = null;
        
        this.init();
    }
    
    /**
     * Initialize the application
     */
    init() {
        // Check authentication first
        if (!this.checkAuth()) {
            return;
        }
        
        this.loadCurrentUser();
        this.setupEventListeners();
        this.connectWebSocket();
        this.navigateTo('dashboard');
        this.startAutoRefresh();
    }
    
    /**
     * Check if user is authenticated
     */
    checkAuth() {
        const token = this.getToken();
        
        if (!token) {
            // Redirect to login page
            window.location.href = 'login.html';
            return false;
        }
        
        return true;
    }
    
    /**
     * Get authentication token
     */
    getToken() {
        return localStorage.getItem('access_token') || sessionStorage.getItem('access_token');
    }
    
    /**
     * Load current user info
     */
    async loadCurrentUser() {
        try {
            const token = this.getToken();
            const response = await fetch(`${CONFIG.API_BASE_URL}/api/v1/auth/me`, {
                headers: {
                    'Authorization': `Bearer ${token}`
                }
            });
            
            if (response.ok) {
                this.currentUser = await response.json();
                this.updateUserDisplay();
            } else {
                // Token invalid, redirect to login
                this.logout();
            }
        } catch (error) {
            console.error('Error loading user:', error);
        }
    }
    
    /**
     * Update user display in UI
     */
    updateUserDisplay() {
        if (this.currentUser) {
            // Update user avatar with name
            const avatar = document.querySelector('.user-avatar');
            if (avatar) {
                avatar.src = `https://ui-avatars.com/api/?name=${encodeURIComponent(this.currentUser.full_name || this.currentUser.username)}&background=10B981&color=fff`;
                avatar.title = `${this.currentUser.full_name || this.currentUser.username} (${this.currentUser.role})`;
            }
        }
    }
    
    /**
     * Logout user
     */
    logout() {
        // Clear tokens
        localStorage.removeItem('access_token');
        localStorage.removeItem('refresh_token');
        localStorage.removeItem('user');
        sessionStorage.removeItem('access_token');
        sessionStorage.removeItem('refresh_token');
        sessionStorage.removeItem('user');
        
        // Redirect to login
        window.location.href = 'login.html';
    }
    
    /**
     * Setup event listeners
     */
    setupEventListeners() {
        // Sidebar navigation
        document.querySelectorAll('.nav-item').forEach(item => {
            item.addEventListener('click', (e) => {
                e.preventDefault();
                const page = item.dataset.page;
                this.navigateTo(page);
            });
        });
        
        // Menu toggle
        document.getElementById('menu-toggle').addEventListener('click', () => {
            document.getElementById('sidebar').classList.toggle('collapsed');
        });
        
        // Refresh button
        document.getElementById('refresh-btn').addEventListener('click', () => {
            this.refreshCurrentPage();
        });
        
        // Logout button
        document.getElementById('logout-btn')?.addEventListener('click', () => {
            this.logout();
        });
        
        // Modal close buttons
        document.querySelectorAll('.modal-close, .modal-cancel').forEach(btn => {
            btn.addEventListener('click', () => {
                this.closeAllModals();
            });
        });
        
        // Add bin button
        document.getElementById('add-bin-btn')?.addEventListener('click', () => {
            this.openModal('add-bin-modal');
        });
        
        // Save bin button
        document.getElementById('save-bin-btn')?.addEventListener('click', () => {
            this.saveBin();
        });
        
        // Filter changes
        document.getElementById('bin-type-filter')?.addEventListener('change', () => {
            this.loadBins();
        });
        document.getElementById('bin-status-filter')?.addEventListener('change', () => {
            this.loadBins();
        });
        document.getElementById('bin-search')?.addEventListener('input', () => {
            this.filterBins();
        });
        
        // Alert filters
        document.getElementById('alert-type-filter')?.addEventListener('change', () => {
            this.loadAlerts();
        });
        document.getElementById('alert-severity-filter')?.addEventListener('change', () => {
            this.loadAlerts();
        });
        document.getElementById('alert-status-filter')?.addEventListener('change', () => {
            this.loadAlerts();
        });
        
        // Check offline sensors
        document.getElementById('check-offline-btn')?.addEventListener('click', () => {
            this.checkOfflineSensors();
        });
        
        // Generate route button
        document.getElementById('generate-route-btn')?.addEventListener('click', () => {
            this.openModal('generate-route-modal');
        });
        
        // Confirm generate route
        document.getElementById('confirm-generate-route-btn')?.addEventListener('click', () => {
            this.generateSmartRoute();
        });
        
        // Resolve alert
        document.getElementById('confirm-resolve-btn')?.addEventListener('click', () => {
            this.confirmResolveAlert();
        });
        
        // Close modals on outside click
        document.querySelectorAll('.modal').forEach(modal => {
            modal.addEventListener('click', (e) => {
                if (e.target === modal) {
                    this.closeAllModals();
                }
            });
        });
    }
    
    /**
     * Navigate to a page
     */
    navigateTo(page) {
        // Update sidebar
        document.querySelectorAll('.nav-item').forEach(item => {
            item.classList.toggle('active', item.dataset.page === page);
        });
        
        // Update page visibility
        document.querySelectorAll('.page').forEach(p => {
            p.classList.toggle('active', p.id === `${page}-page`);
        });
        
        // Update title
        const titles = {
            'dashboard': 'Dashboard',
            'bins': 'Waste Bins',
            'analytics': 'Analytics',
            'routes': 'Collection Routes',
            'alerts': 'Alerts',
            'map': 'Live Map'
        };
        document.getElementById('page-title').textContent = titles[page] || page;
        
        this.currentPage = page;
        
        // Load page data
        this.loadPageData(page);
    }
    
    /**
     * Load data for the current page
     */
    loadPageData(page) {
        switch (page) {
            case 'dashboard':
                this.loadDashboard();
                break;
            case 'bins':
                this.loadBins();
                break;
            case 'analytics':
                this.loadAnalytics();
                break;
            case 'routes':
                this.loadRoutes();
                break;
            case 'alerts':
                this.loadAlerts();
                break;
            case 'map':
                this.loadMap();
                break;
        }
    }
    
    /**
     * Refresh current page
     */
    refreshCurrentPage() {
        this.loadPageData(this.currentPage);
        this.showToast('Data refreshed', 'success');
    }
    
    // ============== Dashboard ==============
    
    async loadDashboard() {
        try {
            // Load stats
            const stats = await api.getDashboardStats();
            this.updateDashboardStats(stats);
            
            // Load charts
            const trends = await api.getFillTrends(30);
            chartManager.createFillTrendChart('fill-trend-chart', trends);
            
            const distribution = await api.getBinStatusDistribution();
            chartManager.createStatusDistributionChart('status-distribution-chart', distribution);
            
            // Load critical alerts
            const alerts = await api.getUnresolvedAlerts('critical');
            this.renderCriticalAlerts(alerts.slice(0, 5));
            
            // Load priority bins
            const bins = await api.getBins({ include_latest: true });
            const priorityBins = bins
                .filter(b => b.latest_reading && b.latest_reading.fill_level_percent >= 70)
                .sort((a, b) => (b.latest_reading?.fill_level_percent || 0) - (a.latest_reading?.fill_level_percent || 0))
                .slice(0, 5);
            this.renderPriorityBins(priorityBins);
            
        } catch (error) {
            console.error('Error loading dashboard:', error);
            this.showToast('Failed to load dashboard data', 'error');
        }
    }
    
    updateDashboardStats(stats) {
        document.getElementById('total-bins').textContent = stats.total_bins || 0;
        document.getElementById('active-bins').textContent = stats.active_bins || 0;
        document.getElementById('high-fill-bins').textContent = stats.high_fill_bins || 0;
        document.getElementById('critical-bins').textContent = stats.critical_bins || 0;
        document.getElementById('collections-today').textContent = stats.total_collections_today || 0;
        document.getElementById('unresolved-alerts').textContent = stats.unresolved_alerts || 0;
        
        // Update alert badges
        const alertCount = stats.unresolved_alerts || 0;
        document.getElementById('alert-badge').textContent = alertCount;
        document.getElementById('header-alert-badge').textContent = alertCount;
        document.getElementById('alert-badge').style.display = alertCount > 0 ? 'block' : 'none';
        document.getElementById('header-alert-badge').style.display = alertCount > 0 ? 'block' : 'none';
    }
    
    renderCriticalAlerts(alerts) {
        const container = document.getElementById('critical-alerts-list');
        
        if (alerts.length === 0) {
            container.innerHTML = '<div class="empty-state"><p>No critical alerts</p></div>';
            return;
        }
        
        container.innerHTML = alerts.map(alert => `
            <div class="alert-item">
                <div class="alert-icon ${alert.severity}">
                    <i class="fas fa-exclamation"></i>
                </div>
                <div class="alert-content">
                    <div class="alert-title">${alert.bin_location || `Bin #${alert.bin_id}`}</div>
                    <div class="alert-meta">${alert.message}</div>
                </div>
                <div class="alert-actions">
                    <button class="btn-sm btn-resolve" onclick="app.openResolveModal(${alert.id})">
                        Resolve
                    </button>
                </div>
            </div>
        `).join('');
    }
    
    renderPriorityBins(bins) {
        const container = document.getElementById('priority-bins-list');
        
        if (bins.length === 0) {
            container.innerHTML = '<div class="empty-state"><p>No bins need collection</p></div>';
            return;
        }
        
        container.innerHTML = bins.map(bin => {
            const fillLevel = bin.latest_reading?.fill_level_percent || 0;
            const fillClass = fillLevel >= 95 ? 'critical' : fillLevel >= 80 ? 'high' : 'medium';
            
            return `
                <div class="bin-item">
                    <div class="alert-icon ${fillClass}">
                        <i class="fas fa-trash"></i>
                    </div>
                    <div class="bin-content">
                        <div class="bin-name">${bin.location_name}</div>
                        <div class="bin-meta">${fillLevel.toFixed(1)}% full - ${bin.bin_type}</div>
                    </div>
                    <div class="alert-actions">
                        <button class="btn-sm btn-resolve" onclick="app.collectBin(${bin.id})">
                            Collect
                        </button>
                    </div>
                </div>
            `;
        }).join('');
    }
    
    // ============== Bins Page ==============
    
    async loadBins() {
        try {
            const typeFilter = document.getElementById('bin-type-filter')?.value;
            const statusFilter = document.getElementById('bin-status-filter')?.value;
            
            const params = { include_latest: true };
            if (typeFilter) params.bin_type = typeFilter;
            if (statusFilter) params.status = statusFilter;
            
            this.bins = await api.getBins(params);
            this.renderBins(this.bins);
        } catch (error) {
            console.error('Error loading bins:', error);
            this.showToast('Failed to load bins', 'error');
        }
    }
    
    renderBins(bins) {
        const container = document.getElementById('bins-grid');
        
        if (bins.length === 0) {
            container.innerHTML = '<div class="empty-state"><p>No bins found</p></div>';
            return;
        }
        
        container.innerHTML = bins.map(bin => {
            const fillLevel = bin.latest_reading?.fill_level_percent || 0;
            const batteryLevel = bin.latest_reading?.battery_percent || 100;
            
            let fillClass = 'low';
            if (fillLevel >= 95) fillClass = 'critical';
            else if (fillLevel >= 80) fillClass = 'high';
            else if (fillLevel >= 50) fillClass = 'medium';
            
            const batteryClass = batteryLevel < 20 ? 'low' : '';
            
            return `
                <div class="bin-card">
                    <div class="bin-card-header">
                        <div>
                            <div class="bin-card-title">${bin.location_name}</div>
                            <div class="bin-card-type ${bin.bin_type}">${bin.bin_type}</div>
                        </div>
                    </div>
                    <div class="bin-fill-bar">
                        <div class="bin-fill-progress ${fillClass}" style="width: ${fillLevel}%"></div>
                    </div>
                    <div class="bin-fill-info">
                        <span>${fillLevel.toFixed(1)}% Full</span>
                        <span>${bin.capacity_liters}L Capacity</span>
                    </div>
                    <div class="bin-card-footer">
                        <div class="bin-battery ${batteryClass}">
                            <i class="fas fa-battery-${batteryLevel > 50 ? 'full' : batteryLevel > 20 ? 'half' : 'empty'}"></i>
                            <span>${batteryLevel.toFixed(0)}%</span>
                        </div>
                        <div class="bin-actions">
                            <button class="btn-action" onclick="app.collectBin(${bin.id})" title="Mark Collected">
                                <i class="fas fa-check"></i>
                            </button>
                            <button class="btn-action" onclick="app.deleteBin(${bin.id})" title="Delete">
                                <i class="fas fa-trash"></i>
                            </button>
                        </div>
                    </div>
                </div>
            `;
        }).join('');
    }
    
    filterBins() {
        const search = document.getElementById('bin-search')?.value.toLowerCase() || '';
        const filtered = this.bins.filter(bin => 
            bin.location_name.toLowerCase().includes(search)
        );
        this.renderBins(filtered);
    }
    
    async saveBin() {
        try {
            const binData = {
                location_name: document.getElementById('bin-location').value,
                latitude: parseFloat(document.getElementById('bin-lat').value),
                longitude: parseFloat(document.getElementById('bin-lon').value),
                bin_type: document.getElementById('bin-type').value,
                capacity_liters: parseInt(document.getElementById('bin-capacity').value)
            };
            
            await api.createBin(binData);
            this.closeAllModals();
            this.showToast('Bin created successfully', 'success');
            this.loadBins();
            
            // Reset form
            document.getElementById('add-bin-form').reset();
        } catch (error) {
            console.error('Error creating bin:', error);
            this.showToast('Failed to create bin', 'error');
        }
    }
    
    async deleteBin(binId) {
        if (!confirm('Are you sure you want to delete this bin?')) return;
        
        try {
            await api.deleteBin(binId);
            this.showToast('Bin deleted', 'success');
            this.loadBins();
        } catch (error) {
            console.error('Error deleting bin:', error);
            this.showToast('Failed to delete bin', 'error');
        }
    }
    
    async collectBin(binId) {
        try {
            await api.collectBin(binId);
            this.showToast('Collection recorded', 'success');
            this.refreshCurrentPage();
        } catch (error) {
            console.error('Error collecting bin:', error);
            this.showToast('Failed to record collection', 'error');
        }
    }
    
    // ============== Analytics Page ==============
    
    async loadAnalytics() {
        try {
            // Load efficiency metrics
            const metrics = await api.getEfficiencyMetrics(30);
            document.getElementById('eff-total-collections').textContent = metrics.total_collections || 0;
            document.getElementById('eff-avg-fill').textContent = (metrics.avg_fill_at_collection || 0).toFixed(1) + '%';
            document.getElementById('eff-collections-per-day').textContent = (metrics.collections_per_day || 0).toFixed(1);
            document.getElementById('eff-fuel-score').textContent = (metrics.fuel_efficiency_score || 0).toFixed(0);
            document.getElementById('eff-cost-savings').textContent = (metrics.cost_savings_percent || 0).toFixed(1) + '%';
            
            // Load charts
            chartManager.createEfficiencyChart('efficiency-chart', {});
            
            const patterns = await api.getFillPatterns(null, 7);
            if (patterns.length > 0) {
                chartManager.createHourlyPatternChart('hourly-pattern-chart', patterns[0]);
            }
            
            const zones = await api.getZoneAnalysis();
            chartManager.createZoneChart('zone-chart', zones);
            
            chartManager.createPredictionChart('prediction-chart', {});
            
        } catch (error) {
            console.error('Error loading analytics:', error);
            this.showToast('Failed to load analytics', 'error');
        }
    }
    
    // ============== Routes Page ==============
    
    async loadRoutes() {
        try {
            const routes = await api.getRoutes();
            this.renderRoutes(routes);
        } catch (error) {
            console.error('Error loading routes:', error);
            this.showToast('Failed to load routes', 'error');
        }
    }
    
    renderRoutes(routes) {
        const container = document.getElementById('routes-list');
        
        if (routes.length === 0) {
            container.innerHTML = '<div class="empty-state"><p>No routes found</p></div>';
            return;
        }
        
        container.innerHTML = routes.map(route => `
            <div class="route-item" onclick="app.selectRoute(${route.id})">
                <div class="route-name">${route.route_name}</div>
                <div class="route-meta">
                    <span><i class="fas fa-calendar"></i> ${new Date(route.scheduled_date).toLocaleDateString()}</span>
                    <span><i class="fas fa-road"></i> ${(route.total_distance_km || 0).toFixed(1)} km</span>
                </div>
                <span class="route-status ${route.status}">${route.status.replace('_', ' ')}</span>
            </div>
        `).join('');
    }
    
    async selectRoute(routeId) {
        try {
            const route = await api.getRoute(routeId);
            const stops = await api.getRouteStops(routeId);
            
            const detailPanel = document.getElementById('route-detail');
            detailPanel.innerHTML = `
                <div class="route-detail">
                    <h3>${route.route_name}</h3>
                    <div class="route-info">
                        <p><strong>Status:</strong> <span class="route-status ${route.status}">${route.status.replace('_', ' ')}</span></p>
                        <p><strong>Scheduled:</strong> ${new Date(route.scheduled_date).toLocaleString()}</p>
                        <p><strong>Distance:</strong> ${(route.total_distance_km || 0).toFixed(1)} km</p>
                        <p><strong>Duration:</strong> ${route.estimated_duration_minutes || 0} min</p>
                        <p><strong>Vehicle:</strong> ${route.vehicle_id || 'Not assigned'}</p>
                        <p><strong>Driver:</strong> ${route.driver_name || 'Not assigned'}</p>
                    </div>
                    <h4>Stops (${stops.length})</h4>
                    <div class="route-stops">
                        ${stops.map((stop, i) => `
                            <div class="route-stop">
                                <span class="stop-number">${i + 1}</span>
                                <span class="stop-name">${stop.location}</span>
                                <span class="stop-fill">${stop.fill_level?.toFixed(0) || 0}%</span>
                            </div>
                        `).join('')}
                    </div>
                    <div class="route-actions">
                        ${route.status === 'planned' ? `
                            <button class="btn btn-primary" onclick="app.startRoute(${route.id})">
                                <i class="fas fa-play"></i> Start Route
                            </button>
                        ` : ''}
                        ${route.status === 'in_progress' ? `
                            <button class="btn btn-primary" onclick="app.completeRoute(${route.id})">
                                <i class="fas fa-check"></i> Complete Route
                            </button>
                        ` : ''}
                    </div>
                </div>
            `;
            
            // Highlight selected route
            document.querySelectorAll('.route-item').forEach(item => {
                item.classList.remove('active');
            });
            event.currentTarget?.classList.add('active');
            
        } catch (error) {
            console.error('Error loading route details:', error);
        }
    }
    
    async generateSmartRoute() {
        try {
            const zone = document.getElementById('route-zone').value;
            const maxBins = parseInt(document.getElementById('max-bins').value);
            const minFill = parseInt(document.getElementById('min-fill').value);
            
            this.closeAllModals();
            this.showToast('Generating optimized route...', 'info');
            
            const result = await api.generateSmartRoute(zone, maxBins, minFill);
            
            if (result.message) {
                this.showToast(result.message, 'warning');
            } else {
                this.showToast(`Route generated: ${result.total_bins} bins, ${result.estimated_distance_km} km`, 'success');
                this.loadRoutes();
            }
        } catch (error) {
            console.error('Error generating route:', error);
            this.showToast('Failed to generate route', 'error');
        }
    }
    
    async startRoute(routeId) {
        try {
            await api.startRoute(routeId);
            this.showToast('Route started', 'success');
            this.loadRoutes();
        } catch (error) {
            console.error('Error starting route:', error);
            this.showToast('Failed to start route', 'error');
        }
    }
    
    async completeRoute(routeId) {
        try {
            await api.completeRoute(routeId);
            this.showToast('Route completed', 'success');
            this.loadRoutes();
        } catch (error) {
            console.error('Error completing route:', error);
            this.showToast('Failed to complete route', 'error');
        }
    }
    
    // ============== Alerts Page ==============
    
    async loadAlerts() {
        try {
            const typeFilter = document.getElementById('alert-type-filter')?.value;
            const severityFilter = document.getElementById('alert-severity-filter')?.value;
            const statusFilter = document.getElementById('alert-status-filter')?.value;
            
            const params = {};
            if (typeFilter) params.alert_type = typeFilter;
            if (severityFilter) params.severity = severityFilter;
            if (statusFilter) params.is_resolved = statusFilter;
            
            this.alerts = await api.getAlerts(params);
            this.renderAlerts(this.alerts);
        } catch (error) {
            console.error('Error loading alerts:', error);
            this.showToast('Failed to load alerts', 'error');
        }
    }
    
    renderAlerts(alerts) {
        const tbody = document.querySelector('#alerts-table tbody');
        
        if (alerts.length === 0) {
            tbody.innerHTML = '<tr><td colspan="7" class="loading">No alerts found</td></tr>';
            return;
        }
        
        tbody.innerHTML = alerts.map(alert => `
            <tr>
                <td>${new Date(alert.created_at).toLocaleString()}</td>
                <td>${alert.bin_location || `Bin #${alert.bin_id}`}</td>
                <td>${alert.alert_type.replace(/_/g, ' ')}</td>
                <td><span class="severity-badge ${alert.severity}">${alert.severity}</span></td>
                <td>${alert.message}</td>
                <td><span class="status-badge ${alert.is_resolved ? 'resolved' : 'unresolved'}">${alert.is_resolved ? 'Resolved' : 'Unresolved'}</span></td>
                <td>
                    ${!alert.is_resolved ? `
                        <button class="btn-sm btn-resolve" onclick="app.openResolveModal(${alert.id})">Resolve</button>
                    ` : '-'}
                </td>
            </tr>
        `).join('');
    }
    
    openResolveModal(alertId) {
        document.getElementById('resolve-alert-id').value = alertId;
        this.openModal('resolve-alert-modal');
    }
    
    async confirmResolveAlert() {
        try {
            const alertId = document.getElementById('resolve-alert-id').value;
            const resolvedBy = document.getElementById('resolved-by').value || 'system';
            const notes = document.getElementById('resolution-notes').value;
            
            await api.resolveAlert(alertId, resolvedBy, notes);
            this.closeAllModals();
            this.showToast('Alert resolved', 'success');
            this.loadAlerts();
        } catch (error) {
            console.error('Error resolving alert:', error);
            this.showToast('Failed to resolve alert', 'error');
        }
    }
    
    async checkOfflineSensors() {
        try {
            this.showToast('Checking for offline sensors...', 'info');
            const result = await api.checkOfflineSensors(120);
            
            if (result.offline_count > 0) {
                this.showToast(`Found ${result.offline_count} offline sensors`, 'warning');
            } else {
                this.showToast('All sensors are online', 'success');
            }
            
            this.loadAlerts();
        } catch (error) {
            console.error('Error checking offline sensors:', error);
            this.showToast('Failed to check offline sensors', 'error');
        }
    }
    
    // ============== Map Page ==============
    
    async loadMap() {
        if (!mapManager.map) {
            mapManager.initMap('live-map');
        }
        
        try {
            const bins = await api.getBins({ include_latest: true });
            mapManager.updateBinMarkers(bins);
            mapManager.resize();
        } catch (error) {
            console.error('Error loading map:', error);
        }
    }
    
    // ============== WebSocket ==============
    
    connectWebSocket() {
        try {
            this.ws = new WebSocket(CONFIG.WS_URL);
            
            this.ws.onopen = () => {
                console.log('WebSocket connected');
                this.wsReconnectAttempts = 0;
                this.updateConnectionStatus(true);
            };
            
            this.ws.onmessage = (event) => {
                const message = JSON.parse(event.data);
                this.handleWebSocketMessage(message);
            };
            
            this.ws.onclose = () => {
                console.log('WebSocket disconnected');
                this.updateConnectionStatus(false);
                this.reconnectWebSocket();
            };
            
            this.ws.onerror = (error) => {
                console.error('WebSocket error:', error);
            };
            
        } catch (error) {
            console.error('Error connecting WebSocket:', error);
        }
    }
    
    reconnectWebSocket() {
        if (this.wsReconnectAttempts < CONFIG.WS_MAX_RECONNECT_ATTEMPTS) {
            this.wsReconnectAttempts++;
            console.log(`Reconnecting WebSocket (attempt ${this.wsReconnectAttempts})...`);
            setTimeout(() => this.connectWebSocket(), CONFIG.WS_RECONNECT_INTERVAL);
        }
    }
    
    handleWebSocketMessage(message) {
        switch (message.type) {
            case 'sensor_update':
                // Update dashboard if on dashboard page
                if (this.currentPage === 'dashboard') {
                    this.loadDashboard();
                }
                // Update map if on map page
                if (this.currentPage === 'map' && mapManager.map) {
                    this.loadMap();
                }
                break;
                
            case 'alert':
                this.showToast(`New Alert: ${message.data.message}`, 'warning');
                if (this.currentPage === 'alerts') {
                    this.loadAlerts();
                }
                break;
        }
    }
    
    updateConnectionStatus(connected) {
        const statusEl = document.getElementById('connection-status');
        const dot = statusEl.querySelector('.status-dot');
        const text = statusEl.querySelector('.status-text');
        
        if (connected) {
            dot.classList.add('online');
            text.textContent = 'Connected';
        } else {
            dot.classList.remove('online');
            text.textContent = 'Disconnected';
        }
    }
    
    // ============== Auto Refresh ==============
    
    startAutoRefresh() {
        // Dashboard refresh
        this.refreshIntervals.dashboard = setInterval(() => {
            if (this.currentPage === 'dashboard') {
                this.loadDashboard();
            }
        }, CONFIG.DASHBOARD_REFRESH_INTERVAL);
        
        // Alerts refresh
        this.refreshIntervals.alerts = setInterval(() => {
            if (this.currentPage === 'alerts') {
                this.loadAlerts();
            }
        }, CONFIG.ALERTS_REFRESH_INTERVAL);
        
        // Map refresh
        this.refreshIntervals.map = setInterval(() => {
            if (this.currentPage === 'map') {
                this.loadMap();
            }
        }, CONFIG.MAP_REFRESH_INTERVAL);
    }
    
    // ============== Modals ==============
    
    openModal(modalId) {
        document.getElementById(modalId).classList.add('active');
    }
    
    closeAllModals() {
        document.querySelectorAll('.modal').forEach(modal => {
            modal.classList.remove('active');
        });
    }
    
    // ============== Toast Notifications ==============
    
    showToast(message, type = 'info') {
        const container = document.getElementById('toast-container');
        
        const icons = {
            success: 'check-circle',
            error: 'exclamation-circle',
            warning: 'exclamation-triangle',
            info: 'info-circle'
        };
        
        const toast = document.createElement('div');
        toast.className = `toast ${type}`;
        toast.innerHTML = `
            <i class="fas fa-${icons[type]} toast-icon"></i>
            <div class="toast-content">
                <div class="toast-message">${message}</div>
            </div>
            <button class="toast-close" onclick="this.parentElement.remove()">
                <i class="fas fa-times"></i>
            </button>
        `;
        
        container.appendChild(toast);
        
        // Auto remove after 5 seconds
        setTimeout(() => {
            toast.remove();
        }, 5000);
    }
}

// Initialize app when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    window.app = new SmartWasteApp();
});
