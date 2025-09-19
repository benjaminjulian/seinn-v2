class AnalyticsView {
    constructor() {
        this.speedMap = null;
        this.routeChart = null;
        this.delayHistogram = null;
        this.speedTimeFilter = 24;
        this.routeTimeFilter = 24;
        this.worstTimeFilter = 24;
        this.histogramTimeFilter = 24;

        this.initEventListeners();
        this.loadSystemStats();
        this.initSpeedMap();
        this.loadSpeedData();
        this.loadRouteStats();
        this.loadStationRoutePairs();
        this.loadDelayHistogram();
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
            });
        });

        // Worst station-route pairs time filter
        document.querySelectorAll('input[name="worstTimeFilter"]').forEach(radio => {
            radio.addEventListener('change', (e) => {
                this.worstTimeFilter = parseInt(e.target.value);
                this.loadStationRoutePairs();
            });
        });

        // Histogram time filter
        document.querySelectorAll('input[name="histogramTimeFilter"]').forEach(radio => {
            radio.addEventListener('change', (e) => {
                this.histogramTimeFilter = parseInt(e.target.value);
                this.loadDelayHistogram();
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
              .bindPopup(`Leið ${point.route}<br>Hraði: ${speed.toFixed(1)} km/klst`);
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
                <h6>Hraði (km/klst)</h6>
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
                        label: 'Á réttum tíma',
                        data: onTimeData,
                        backgroundColor: 'rgba(40, 167, 69, 0.8)',
                        borderColor: 'rgb(40, 167, 69)',
                        borderWidth: 1
                    },
                    {
                        label: 'Seint',
                        data: lateData,
                        backgroundColor: 'rgba(255, 193, 7, 0.8)',
                        borderColor: 'rgb(255, 193, 7)',
                        borderWidth: 1
                    },
                    {
                        label: 'Snemma',
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
                            text: 'Leið'
                        }
                    },
                    y: {
                        stacked: true,
                        beginAtZero: true,
                        max: 100,
                        title: {
                            display: true,
                            text: 'Prósenta'
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
                tableBody.innerHTML = '<tr><td colspan="5" class="text-center text-danger">Gat ekki hlaðið gögn</td></tr>';
                return;
            }
        }

        if (routeStats.length === 0) {
            tableBody.innerHTML = '<tr><td colspan="5" class="text-center">Engin gögn til staðar</td></tr>';
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

    async loadStationRoutePairs() {
        try {
            const response = await fetch(`/api/analytics/station-route-pairs?hours=${this.worstTimeFilter}`);
            const data = await response.json();

            this.updateStationRoutePairs(data);
        } catch (error) {
            console.error('Error loading station-route pairs:', error);
        }
    }

    updateStationRoutePairs(data) {
        // Update most delayed pairs
        const mostDelayedDiv = document.getElementById('mostDelayed');
        if (data.most_delayed && data.most_delayed.length > 0) {
            mostDelayedDiv.innerHTML = data.most_delayed.map(pair => {
                const avgDelayMin = Math.round(pair.avg_delay_seconds / 60);
                return `
                    <div class="card mb-2">
                        <div class="card-body py-2">
                            <h6 class="mb-1">
                                <span class="badge bg-primary">${pair.route_short_name}</span>
                                ${pair.stop_name}
                            </h6>
                            <small class="text-muted">
                                Meðaltöf: <span class="text-danger">+${avgDelayMin} mín</span>
                                (${pair.arrival_count} komur)
                            </small>
                        </div>
                    </div>
                `;
            }).join('');
        } else {
            mostDelayedDiv.innerHTML = '<p class="text-muted">Engin gögn til staðar</p>';
        }

        // Update earliest pairs
        const mostEarlyDiv = document.getElementById('mostEarly');
        if (data.most_early && data.most_early.length > 0) {
            mostEarlyDiv.innerHTML = data.most_early.map(pair => {
                const avgDelayMin = Math.round(Math.abs(pair.avg_delay_seconds) / 60);
                return `
                    <div class="card mb-2">
                        <div class="card-body py-2">
                            <h6 class="mb-1">
                                <span class="badge bg-primary">${pair.route_short_name}</span>
                                ${pair.stop_name}
                            </h6>
                            <small class="text-muted">
                                Fyrirtækni: <span class="text-success">-${avgDelayMin} mín</span>
                                (${pair.arrival_count} komur)
                            </small>
                        </div>
                    </div>
                `;
            }).join('');
        } else {
            mostEarlyDiv.innerHTML = '<p class="text-muted">Engin gögn til staðar</p>';
        }
    }

    async loadDelayHistogram() {
        try {
            const response = await fetch(`/api/analytics/delay-histogram?hours=${this.histogramTimeFilter}`);
            const data = await response.json();

            this.updateDelayHistogram(data);
        } catch (error) {
            console.error('Error loading delay histogram:', error);
        }
    }

    updateDelayHistogram(routeData) {
        const ctx = document.getElementById('delayHistogram').getContext('2d');

        if (this.delayHistogram) {
            this.delayHistogram.destroy();
        }

        if (routeData.length === 0) {
            ctx.fillText('Engin gögn til staðar', 50, 50);
            return;
        }

        // Update the route stats table with histogram data
        this.updateRouteStatsTableWithHistogram(routeData);

        // Create histogram chart for top 10 routes
        const topRoutes = routeData.slice(0, 10);
        const labels = topRoutes.map(route => route.route_short_name || route.route_id);

        const datasets = [
            {
                label: 'Mjög snemma (< -2 mín)',
                data: topRoutes.map(r => r.very_early),
                backgroundColor: 'rgba(13, 110, 253, 0.8)'
            },
            {
                label: 'Snemma (-2 til -1 mín)',
                data: topRoutes.map(r => r.early),
                backgroundColor: 'rgba(32, 201, 151, 0.8)'
            },
            {
                label: 'Aðeins snemma (-1 til 0 mín)',
                data: topRoutes.map(r => r.slightly_early),
                backgroundColor: 'rgba(111, 207, 151, 0.8)'
            },
            {
                label: 'Á réttum tíma (±1 mín)',
                data: topRoutes.map(r => r.on_time),
                backgroundColor: 'rgba(40, 167, 69, 0.8)'
            },
            {
                label: 'Aðeins seint (1-3 mín)',
                data: topRoutes.map(r => r.slightly_late),
                backgroundColor: 'rgba(255, 193, 7, 0.8)'
            },
            {
                label: 'Seint (3-5 mín)',
                data: topRoutes.map(r => r.late),
                backgroundColor: 'rgba(253, 126, 20, 0.8)'
            },
            {
                label: 'Mjög seint (> 5 mín)',
                data: topRoutes.map(r => r.very_late),
                backgroundColor: 'rgba(220, 53, 69, 0.8)'
            }
        ];

        this.delayHistogram = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: labels,
                datasets: datasets
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    x: {
                        stacked: true,
                        title: {
                            display: true,
                            text: 'Leið'
                        }
                    },
                    y: {
                        stacked: true,
                        beginAtZero: true,
                        title: {
                            display: true,
                            text: 'Fjöldi komu'
                        }
                    }
                },
                plugins: {
                    legend: {
                        position: 'bottom'
                    },
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                const percentage = Math.round(context.raw / topRoutes[context.dataIndex].total_arrivals * 100);
                                return `${context.dataset.label}: ${context.raw} (${percentage}%)`;
                            }
                        }
                    }
                }
            }
        });
    }

    updateRouteStatsTableWithHistogram(routeData) {
        const tableBody = document.querySelector('#routeStatsTable tbody');

        if (routeData.length === 0) {
            tableBody.innerHTML = '<tr><td colspan="5" class="text-center">Engin gögn til staðar</td></tr>';
            return;
        }

        tableBody.innerHTML = routeData.map(route => {
            const onTimePercent = Math.round(route.on_time / route.total_arrivals * 100);
            const avgDelayMin = Math.round(route.avg_delay / 60);

            // Create histogram visualization
            const histogramData = {
                very_early: Math.round(route.very_early / route.total_arrivals * 100),
                early: Math.round(route.early / route.total_arrivals * 100),
                slightly_early: Math.round(route.slightly_early / route.total_arrivals * 100),
                on_time: Math.round(route.on_time / route.total_arrivals * 100),
                slightly_late: Math.round(route.slightly_late / route.total_arrivals * 100),
                late: Math.round(route.late / route.total_arrivals * 100),
                very_late: Math.round(route.very_late / route.total_arrivals * 100)
            };

            const histogramBars = `
                <div class="histogram-bar">
                    ${histogramData.very_early > 0 ? `<div class="bar bar-very-early" style="width: ${histogramData.very_early}%" title="Mjög snemma: ${histogramData.very_early}%"></div>` : ''}
                    ${histogramData.early > 0 ? `<div class="bar bar-early" style="width: ${histogramData.early}%" title="Snemma: ${histogramData.early}%"></div>` : ''}
                    ${histogramData.slightly_early > 0 ? `<div class="bar bar-slightly-early" style="width: ${histogramData.slightly_early}%" title="Aðeins snemma: ${histogramData.slightly_early}%"></div>` : ''}
                    ${histogramData.on_time > 0 ? `<div class="bar bar-on-time" style="width: ${histogramData.on_time}%" title="Á réttum tíma: ${histogramData.on_time}%"></div>` : ''}
                    ${histogramData.slightly_late > 0 ? `<div class="bar bar-slightly-late" style="width: ${histogramData.slightly_late}%" title="Aðeins seint: ${histogramData.slightly_late}%"></div>` : ''}
                    ${histogramData.late > 0 ? `<div class="bar bar-late" style="width: ${histogramData.late}%" title="Seint: ${histogramData.late}%"></div>` : ''}
                    ${histogramData.very_late > 0 ? `<div class="bar bar-very-late" style="width: ${histogramData.very_late}%" title="Mjög seint: ${histogramData.very_late}%"></div>` : ''}
                </div>
            `;

            return `
                <tr>
                    <td><span class="route-badge">${route.route_short_name || route.route_id}</span></td>
                    <td>${route.total_arrivals}</td>
                    <td class="delay-${avgDelayMin > 0 ? 'positive' : avgDelayMin < 0 ? 'negative' : 'neutral'}">
                        ${avgDelayMin > 0 ? '+' : ''}${avgDelayMin} mín
                    </td>
                    <td><span class="text-success">${onTimePercent}%</span></td>
                    <td>${histogramBars}</td>
                </tr>
            `;
        }).join('');
    }
}

// Initialize when page loads
document.addEventListener('DOMContentLoaded', () => {
    new AnalyticsView();
});