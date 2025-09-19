class AnalyticsView {
    constructor() {
        this.speedMap = null;
        this.routeChart = null;
        this.speedTimeFilter = 24;
        this.routeTimeFilter = 24;

        this.initEventListeners();
        this.loadSystemStats();
        this.initSpeedMap();
        this.loadSpeedData();
        this.loadRouteStats();
    }

    initEventListeners() {
        // Speed time filter
        document.querySelectorAll('input[name="speedTimeFilter"]').forEach(radio => {
            radio.addEventListener('change', (e) => {
                this.speedTimeFilter = parseInt(e.target.value);
                this.loadSpeedData();
            });
        });

        // Route time filter
        document.querySelectorAll('input[name="routeTimeFilter"]').forEach(radio => {
            radio.addEventListener('change', (e) => {
                this.routeTimeFilter = parseInt(e.target.value);
                this.loadRouteStats();
                this.updateRouteStatsTable();
            });
        });
    }

    async loadSystemStats() {
        try {
            const response = await fetch('/api/analytics/system-stats');
            const stats = await response.json();

            document.getElementById('totalRecords').textContent = this.formatNumber(stats.total_records);
            document.getElementById('uniqueRoutes').textContent = stats.unique_routes;
            document.getElementById('recentRecords').textContent = this.formatNumber(stats.recent_records);
            document.getElementById('recentDelays').textContent = this.formatNumber(stats.recent_delays);
        } catch (error) {
            console.error('Error loading system stats:', error);
        }
    }

    initSpeedMap() {
        // Initialize map centered on Reykjavik
        this.speedMap = L.map('speedMap').setView([64.1466, -21.9426], 11);

        L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
            attribution: '© OpenStreetMap contributors'
        }).addTo(this.speedMap);
    }

    async loadSpeedData() {
        try {
            const response = await fetch(`/api/analytics/speed-data?hours=${this.speedTimeFilter}`);
            const speedData = await response.json();

            this.updateSpeedMap(speedData);
        } catch (error) {
            console.error('Error loading speed data:', error);
        }
    }

    updateSpeedMap(speedData) {
        // Clear existing markers
        this.speedMap.eachLayer(layer => {
            if (layer instanceof L.CircleMarker) {
                this.speedMap.removeLayer(layer);
            }
        });

        if (speedData.length === 0) {
            return;
        }

        // Add speed points
        speedData.forEach(point => {
            const speed = point.speed_kmh;
            let color, radius;

            // Color based on speed
            if (speed < 10) {
                color = '#dc3545'; // Red - very slow
                radius = 3;
            } else if (speed < 20) {
                color = '#fd7e14'; // Orange - slow
                radius = 4;
            } else if (speed < 40) {
                color = '#ffc107'; // Yellow - moderate
                radius = 5;
            } else if (speed < 60) {
                color = '#20c997'; // Teal - fast
                radius = 6;
            } else {
                color = '#198754'; // Green - very fast
                radius = 7;
            }

            L.circleMarker([point.latitude, point.longitude], {
                color: color,
                fillColor: color,
                fillOpacity: 0.6,
                radius: radius,
                weight: 1
            }).addTo(this.speedMap)
              .bindPopup(`Route ${point.route}<br>Speed: ${speed.toFixed(1)} km/h`);
        });

        // Add legend
        this.addSpeedMapLegend();
    }

    addSpeedMapLegend() {
        const legend = L.control({ position: 'bottomright' });

        legend.onAdd = function() {
            const div = L.DomUtil.create('div', 'info legend');
            div.style.backgroundColor = 'white';
            div.style.padding = '10px';
            div.style.border = '2px solid #ccc';
            div.style.borderRadius = '5px';

            div.innerHTML = `
                <h6>Speed (km/h)</h6>
                <div><span style="color: #dc3545; font-size: 20px;">●</span> < 10</div>
                <div><span style="color: #fd7e14; font-size: 20px;">●</span> 10-20</div>
                <div><span style="color: #ffc107; font-size: 20px;">●</span> 20-40</div>
                <div><span style="color: #20c997; font-size: 20px;">●</span> 40-60</div>
                <div><span style="color: #198754; font-size: 20px;">●</span> > 60</div>
            `;

            return div;
        };

        legend.addTo(this.speedMap);
    }

    async loadRouteStats() {
        try {
            const response = await fetch(`/api/analytics/route-stats?hours=${this.routeTimeFilter}`);
            const routeStats = await response.json();

            this.updateRouteChart(routeStats);
            this.updateRouteStatsTable(routeStats);
        } catch (error) {
            console.error('Error loading route stats:', error);
        }
    }

    updateRouteChart(routeStats) {
        const ctx = document.getElementById('routeChart').getContext('2d');

        if (this.routeChart) {
            this.routeChart.destroy();
        }

        if (routeStats.length === 0) {
            ctx.fillText('No data available', 50, 50);
            return;
        }

        // Take top 10 routes by arrivals
        const topRoutes = routeStats.slice(0, 10);

        const labels = topRoutes.map(route => route.route_short_name || route.route_id);
        const onTimeData = topRoutes.map(route => {
            return Math.round(route.on_time / route.total_arrivals * 100);
        });
        const lateData = topRoutes.map(route => {
            return Math.round(route.late / route.total_arrivals * 100);
        });
        const earlyData = topRoutes.map(route => {
            return Math.round(route.early / route.total_arrivals * 100);
        });

        this.routeChart = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: labels,
                datasets: [
                    {
                        label: 'On Time',
                        data: onTimeData,
                        backgroundColor: 'rgba(40, 167, 69, 0.8)',
                        borderColor: 'rgb(40, 167, 69)',
                        borderWidth: 1
                    },
                    {
                        label: 'Late',
                        data: lateData,
                        backgroundColor: 'rgba(255, 193, 7, 0.8)',
                        borderColor: 'rgb(255, 193, 7)',
                        borderWidth: 1
                    },
                    {
                        label: 'Early',
                        data: earlyData,
                        backgroundColor: 'rgba(23, 162, 184, 0.8)',
                        borderColor: 'rgb(23, 162, 184)',
                        borderWidth: 1
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    x: {
                        stacked: true,
                        title: {
                            display: true,
                            text: 'Route'
                        }
                    },
                    y: {
                        stacked: true,
                        beginAtZero: true,
                        max: 100,
                        title: {
                            display: true,
                            text: 'Percentage'
                        }
                    }
                },
                plugins: {
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                return `${context.dataset.label}: ${context.raw}%`;
                            }
                        }
                    }
                }
            }
        });
    }

    async updateRouteStatsTable(routeStats = null) {
        const tableBody = document.querySelector('#routeStatsTable tbody');

        if (!routeStats) {
            try {
                const response = await fetch(`/api/analytics/route-stats?hours=${this.routeTimeFilter}`);
                routeStats = await response.json();
            } catch (error) {
                console.error('Error loading route stats for table:', error);
                tableBody.innerHTML = '<tr><td colspan="6" class="text-center text-danger">Failed to load data</td></tr>';
                return;
            }
        }

        if (routeStats.length === 0) {
            tableBody.innerHTML = '<tr><td colspan="6" class="text-center">No data available</td></tr>';
            return;
        }

        tableBody.innerHTML = routeStats.map(route => {
            const onTimePercent = Math.round(route.on_time / route.total_arrivals * 100);
            const latePercent = Math.round(route.late / route.total_arrivals * 100);
            const veryLatePercent = Math.round(route.very_late / route.total_arrivals * 100);
            const avgDelayMin = Math.round(route.avg_delay / 60);

            return `
                <tr>
                    <td><span class="route-badge">${route.route_short_name || route.route_id}</span></td>
                    <td>${route.total_arrivals}</td>
                    <td class="delay-${avgDelayMin > 0 ? 'positive' : avgDelayMin < 0 ? 'negative' : 'neutral'}">
                        ${avgDelayMin > 0 ? '+' : ''}${avgDelayMin}min
                    </td>
                    <td><span class="text-success">${onTimePercent}%</span></td>
                    <td><span class="text-warning">${latePercent}%</span></td>
                    <td><span class="text-danger">${veryLatePercent}%</span></td>
                </tr>
            `;
        }).join('');
    }

    formatNumber(num) {
        if (num >= 1000000) return (num / 1000000).toFixed(1) + 'M';
        if (num >= 1000) return (num / 1000).toFixed(1) + 'K';
        return num.toString();
    }
}

// Initialize when page loads
document.addEventListener('DOMContentLoaded', () => {
    new AnalyticsView();
});