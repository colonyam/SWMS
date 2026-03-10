/**
 * Smart Waste Management System - Charts
 */

class ChartManager {
    constructor() {
        this.charts = {};
    }
    
    /**
     * Destroy a chart if it exists
     */
    destroyChart(chartId) {
        if (this.charts[chartId]) {
            this.charts[chartId].destroy();
            delete this.charts[chartId];
        }
    }
    
    /**
     * Get common chart options
     */
    getCommonOptions() {
        return {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'bottom',
                    labels: {
                        usePointStyle: true,
                        padding: 15,
                        font: { size: 12 }
                    }
                }
            }
        };
    }
    
    /**
     * Create Fill Trend Chart
     */
    createFillTrendChart(canvasId, data) {
        this.destroyChart(canvasId);
        
        const ctx = document.getElementById(canvasId).getContext('2d');
        
        this.charts[canvasId] = new Chart(ctx, {
            type: 'line',
            data: {
                labels: data.map(d => {
                    const date = new Date(d.date);
                    return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
                }),
                datasets: [{
                    label: 'Average Fill Level (%)',
                    data: data.map(d => d.value),
                    borderColor: CONFIG.CHART_COLORS.primary,
                    backgroundColor: `${CONFIG.CHART_COLORS.primary}20`,
                    fill: true,
                    tension: 0.4,
                    pointRadius: 4,
                    pointBackgroundColor: CONFIG.CHART_COLORS.primary,
                    pointBorderColor: '#fff',
                    pointBorderWidth: 2
                }]
            },
            options: {
                ...this.getCommonOptions(),
                scales: {
                    y: {
                        beginAtZero: true,
                        max: 100,
                        grid: { color: '#E2E8F0' }
                    },
                    x: {
                        grid: { display: false }
                    }
                }
            }
        });
    }
    
    /**
     * Create Status Distribution Chart (Doughnut)
     */
    createStatusDistributionChart(canvasId, data) {
        this.destroyChart(canvasId);
        
        const ctx = document.getElementById(canvasId).getContext('2d');
        
        this.charts[canvasId] = new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: ['Critical (>95%)', 'High (80-95%)', 'Medium (50-80%)', 'Low (20-50%)', 'Empty (<20%)'],
                datasets: [{
                    data: [
                        data.critical_95_100 || 0,
                        data.high_80_95 || 0,
                        data.medium_50_80 || 0,
                        data.low_20_50 || 0,
                        data.empty_0_20 || 0
                    ],
                    backgroundColor: [
                        CONFIG.CHART_COLORS.critical,
                        CONFIG.CHART_COLORS.danger,
                        CONFIG.CHART_COLORS.warning,
                        CONFIG.CHART_COLORS.success,
                        CONFIG.CHART_COLORS.gray
                    ],
                    borderWidth: 0
                }]
            },
            options: {
                ...this.getCommonOptions(),
                cutout: '65%',
                plugins: {
                    ...this.getCommonOptions().plugins,
                    legend: {
                        position: 'right',
                        labels: {
                            usePointStyle: true,
                            padding: 10,
                            font: { size: 11 }
                        }
                    }
                }
            }
        });
    }
    
    /**
     * Create Efficiency Chart
     */
    createEfficiencyChart(canvasId, data) {
        this.destroyChart(canvasId);
        
        const ctx = document.getElementById(canvasId).getContext('2d');
        
        // Generate sample data if none provided
        const labels = ['Week 1', 'Week 2', 'Week 3', 'Week 4'];
        const collections = data.collections || [45, 52, 48, 55];
        const efficiency = data.efficiency || [78, 82, 80, 85];
        
        this.charts[canvasId] = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: labels,
                datasets: [
                    {
                        label: 'Collections',
                        data: collections,
                        backgroundColor: CONFIG.CHART_COLORS.secondary,
                        borderRadius: 4,
                        yAxisID: 'y'
                    },
                    {
                        label: 'Efficiency Score',
                        data: efficiency,
                        type: 'line',
                        borderColor: CONFIG.CHART_COLORS.primary,
                        backgroundColor: 'transparent',
                        borderWidth: 2,
                        pointRadius: 4,
                        yAxisID: 'y1'
                    }
                ]
            },
            options: {
                ...this.getCommonOptions(),
                scales: {
                    y: {
                        type: 'linear',
                        display: true,
                        position: 'left',
                        grid: { color: '#E2E8F0' }
                    },
                    y1: {
                        type: 'linear',
                        display: true,
                        position: 'right',
                        min: 0,
                        max: 100,
                        grid: { display: false }
                    },
                    x: {
                        grid: { display: false }
                    }
                }
            }
        });
    }
    
    /**
     * Create Hourly Pattern Chart
     */
    createHourlyPatternChart(canvasId, data) {
        this.destroyChart(canvasId);
        
        const ctx = document.getElementById(canvasId).getContext('2d');
        
        // Generate hours array
        const hours = Array.from({ length: 24 }, (_, i) => `${i}:00`);
        const hourlyData = data.hourly_avg || Array.from({ length: 24 }, () => Math.random() * 50 + 20);
        
        this.charts[canvasId] = new Chart(ctx, {
            type: 'line',
            data: {
                labels: hours,
                datasets: [{
                    label: 'Average Fill Level (%)',
                    data: hourlyData,
                    borderColor: CONFIG.CHART_COLORS.accent,
                    backgroundColor: `${CONFIG.CHART_COLORS.accent}20`,
                    fill: true,
                    tension: 0.4,
                    pointRadius: 3
                }]
            },
            options: {
                ...this.getCommonOptions(),
                scales: {
                    y: {
                        beginAtZero: true,
                        max: 100,
                        grid: { color: '#E2E8F0' }
                    },
                    x: {
                        grid: { display: false },
                        ticks: {
                            maxTicksLimit: 12
                        }
                    }
                }
            }
        });
    }
    
    /**
     * Create Zone Analysis Chart
     */
    createZoneChart(canvasId, data) {
        this.destroyChart(canvasId);
        
        const ctx = document.getElementById(canvasId).getContext('2d');
        
        const zones = data.map(z => z.zone);
        const fillLevels = data.map(z => z.avg_fill_level);
        
        this.charts[canvasId] = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: zones,
                datasets: [{
                    label: 'Average Fill Level (%)',
                    data: fillLevels,
                    backgroundColor: fillLevels.map(level => {
                        if (level >= 80) return CONFIG.CHART_COLORS.danger;
                        if (level >= 50) return CONFIG.CHART_COLORS.warning;
                        return CONFIG.CHART_COLORS.success;
                    }),
                    borderRadius: 4
                }]
            },
            options: {
                ...this.getCommonOptions(),
                scales: {
                    y: {
                        beginAtZero: true,
                        max: 100,
                        grid: { color: '#E2E8F0' }
                    },
                    x: {
                        grid: { display: false }
                    }
                }
            }
        });
    }
    
    /**
     * Create Prediction Chart
     */
    createPredictionChart(canvasId, data) {
        this.destroyChart(canvasId);
        
        const ctx = document.getElementById(canvasId).getContext('2d');
        
        // Generate next 7 days
        const days = [];
        const current = [];
        const predicted = [];
        
        for (let i = 0; i < 7; i++) {
            const date = new Date();
            date.setDate(date.getDate() + i);
            days.push(date.toLocaleDateString('en-US', { weekday: 'short' }));
            
            // Sample prediction data
            const baseFill = 40 + i * 8;
            current.push(baseFill);
            predicted.push(Math.min(100, baseFill + Math.random() * 15));
        }
        
        this.charts[canvasId] = new Chart(ctx, {
            type: 'line',
            data: {
                labels: days,
                datasets: [
                    {
                        label: 'Current Trend',
                        data: current,
                        borderColor: CONFIG.CHART_COLORS.secondary,
                        backgroundColor: 'transparent',
                        borderWidth: 2,
                        pointRadius: 4
                    },
                    {
                        label: 'Predicted',
                        data: predicted,
                        borderColor: CONFIG.CHART_COLORS.primary,
                        backgroundColor: `${CONFIG.CHART_COLORS.primary}10`,
                        fill: true,
                        borderDash: [5, 5],
                        pointRadius: 4
                    }
                ]
            },
            options: {
                ...this.getCommonOptions(),
                scales: {
                    y: {
                        beginAtZero: true,
                        max: 100,
                        grid: { color: '#E2E8F0' }
                    },
                    x: {
                        grid: { display: false }
                    }
                }
            }
        });
    }
    
    /**
     * Create Bin Fill Gauge
     */
    createBinGauge(canvasId, fillLevel) {
        this.destroyChart(canvasId);
        
        const ctx = document.getElementById(canvasId).getContext('2d');
        
        const color = fillLevel >= 95 ? CONFIG.CHART_COLORS.critical :
                      fillLevel >= 80 ? CONFIG.CHART_COLORS.danger :
                      fillLevel >= 50 ? CONFIG.CHART_COLORS.warning :
                      CONFIG.CHART_COLORS.success;
        
        this.charts[canvasId] = new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: ['Filled', 'Empty'],
                datasets: [{
                    data: [fillLevel, 100 - fillLevel],
                    backgroundColor: [color, '#E2E8F0'],
                    borderWidth: 0
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: true,
                cutout: '75%',
                plugins: {
                    legend: { display: false },
                    tooltip: { enabled: false }
                }
            },
            plugins: [{
                id: 'textCenter',
                beforeDraw: function(chart) {
                    const width = chart.width;
                    const height = chart.height;
                    const ctx = chart.ctx;
                    
                    ctx.restore();
                    const fontSize = (height / 114).toFixed(2);
                    ctx.font = `bold ${fontSize}em sans-serif`;
                    ctx.textBaseline = 'middle';
                    ctx.fillStyle = color;
                    
                    const text = `${Math.round(fillLevel)}%`;
                    const textX = Math.round((width - ctx.measureText(text).width) / 2);
                    const textY = height / 2;
                    
                    ctx.fillText(text, textX, textY);
                    ctx.save();
                }
            }]
        });
    }
}

// Create global chart manager instance
const chartManager = new ChartManager();
