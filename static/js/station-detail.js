class StationDetailView {
    constructor() {
        this.currentTimeFilter = 24;
        this.delayChart = null;
        this.map = null;

        this.initEventListeners();
        this.initMap();
        this.loadDelayData();
    }

    initEventListeners() {
        // Time filter radio buttons
        document.querySelectorAll('input[name="timeFilter"]').forEach(radio => {
            radio.addEventListener('change', (e) => {
                this.currentTimeFilter = parseInt(e.target.value);
                this.loadDelayData();
            });
        });
    }

    initMap() {
        if (stationLat && stationLon) {
            this.map = L.map('stationMap').setView([stationLat, stationLon], 15);

            L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
                attribution: '© OpenStreetMap contributors'
            }).addTo(this.map);

            L.marker([stationLat, stationLon])
                .addTo(this.map)
                .bindPopup(`<b>${stationName}</b><br>Station ID: ${stationId}`)
                .openPopup();
        }
    }

    async loadDelayData() {
        const delayDataDiv = document.getElementById('delayData');
        const routeStatsDiv = document.getElementById('routeStats');

        // Show loading
        delayDataDiv.innerHTML = '<div class="text-center"><div class="spinner-border" role="status"></div></div>';
        routeStatsDiv.innerHTML = '<div class="text-center"><div class="spinner-border" role="status"></div></div>';

        try {
            const response = await fetch(`/api/station/${stationId}/delays?hours=${this.currentTimeFilter}`);
            const data = await response.json();

            this.renderDelayData(data.delays, delayDataDiv);
            this.renderRouteStats(data.stats, routeStatsDiv);
            this.updateDelayChart(data.delays);
        } catch (error) {
            console.error('Error loading delay data:', error);
            delayDataDiv.innerHTML = '<div class="alert alert-danger">Failed to load delay data</div>';
            routeStatsDiv.innerHTML = '<div class="alert alert-danger">Failed to load route statistics</div>';
        }
    }

    renderDelayData(delays, container) {
        if (delays.length === 0) {
            container.innerHTML = '<div class="alert alert-info">No delay data available for the selected time period.</div>';
            return;
        }

        let html = '<div class="table-responsive"><table class="table table-sm">';
        html += '<thead><tr><th>Route</th><th>Time</th><th>Scheduled</th><th>Delay</th></tr></thead><tbody>';

        delays.slice(0, 20).forEach(delay => {
            const delayMin = Math.round(delay.delay_seconds / 60);
            const actualTime = new Date(delay.actual_arrival_time).toLocaleTimeString();
            const scheduledTime = delay.scheduled_arrival_time;

            html += `
                <tr>
                    <td><span class="route-badge">${delay.route_short_name || delay.route_id}</span></td>
                    <td>${actualTime}</td>
                    <td>${scheduledTime}</td>
                    <td class="delay-${delayMin > 0 ? 'positive' : delayMin < 0 ? 'negative' : 'neutral'}">
                        ${delayMin > 0 ? '+' : ''}${delayMin}min
                    </td>
                </tr>
            `;
        });

        html += '</tbody></table></div>';

        if (delays.length > 20) {
            html += `<small class="text-muted">Showing 20 of ${delays.length} recent arrivals</small>`;
        }

        container.innerHTML = html;
    }

    renderRouteStats(stats, container) {
        if (stats.length === 0) {
            container.innerHTML = '<div class="alert alert-info">No route statistics available.</div>';
            return;
        }

        let html = '';

        stats.forEach(stat => {
            const onTimePercent = Math.round((stat.total_arrivals - stat.late_arrivals - stat.early_arrivals) / stat.total_arrivals * 100);
            const latePercent = Math.round(stat.late_arrivals / stat.total_arrivals * 100);
            const earlyPercent = Math.round(stat.early_arrivals / stat.total_arrivals * 100);
            const avgDelayMin = Math.round(stat.avg_delay / 60);

            html += `
                <div class="card mb-3">
                    <div class="card-body">
                        <h6 class="card-title">
                            <span class="route-badge">${stat.route_short_name || stat.route_id}</span>
                        </h6>
                        <div class="row text-center mb-2">
                            <div class="col-4">
                                <strong>${stat.total_arrivals}</strong><br>
                                <small class="text-muted">Arrivals</small>
                            </div>
                            <div class="col-4">
                                <strong class="delay-${avgDelayMin > 0 ? 'positive' : avgDelayMin < 0 ? 'negative' : 'neutral'}">
                                    ${avgDelayMin > 0 ? '+' : ''}${avgDelayMin}min
                                </strong><br>
                                <small class="text-muted">Avg Delay</small>
                            </div>
                            <div class="col-4">
                                <strong class="text-success">${onTimePercent}%</strong><br>
                                <small class="text-muted">On Time</small>
                            </div>
                        </div>
                        <div class="progress" style="height: 8px;">
                            <div class="progress-bar bg-success" style="width: ${onTimePercent}%" title="${onTimePercent}% on time"></div>
                            <div class="progress-bar bg-warning" style="width: ${latePercent}%" title="${latePercent}% late"></div>
                            <div class="progress-bar bg-primary" style="width: ${earlyPercent}%" title="${earlyPercent}% early"></div>
                        </div>
                        <div class="row mt-2 text-center">
                            <div class="col-4">
                                <small class="text-success">${onTimePercent}% On Time</small>
                            </div>
                            <div class="col-4">
                                <small class="text-warning">${latePercent}% Late</small>
                            </div>
                            <div class="col-4">
                                <small class="text-primary">${earlyPercent}% Early</small>
                            </div>
                        </div>
                    </div>
                </div>
            `;
        });

        container.innerHTML = html;
    }

    updateDelayChart(delays) {
        const ctx = document.getElementById('delayChart').getContext('2d');

        // Destroy existing chart if it exists
        if (this.delayChart) {
            this.delayChart.destroy();
        }

        if (delays.length === 0) {
            ctx.fillText('No data available', 50, 50);
            return;
        }

        // Group delays by hour
        const hourlyDelays = {};
        delays.forEach(delay => {
            const hour = new Date(delay.actual_arrival_time).getHours();
            if (!hourlyDelays[hour]) {
                hourlyDelays[hour] = [];
            }
            hourlyDelays[hour].push(delay.delay_seconds / 60); // Convert to minutes
        });

        // Calculate average delay per hour
        const labels = [];
        const data = [];
        const colors = [];

        for (let hour = 0; hour < 24; hour++) {
            const hourDelays = hourlyDelays[hour] || [];
            const avgDelay = hourDelays.length > 0 ?
                hourDelays.reduce((sum, d) => sum + d, 0) / hourDelays.length : 0;

            labels.push(`${hour.toString().padStart(2, '0')}:00`);
            data.push(avgDelay);

            // Color based on delay
            if (avgDelay > 5) colors.push('rgba(220, 53, 69, 0.8)');      // Red for >5min late
            else if (avgDelay > 1) colors.push('rgba(255, 193, 7, 0.8)'); // Yellow for >1min late
            else if (avgDelay > -1) colors.push('rgba(40, 167, 69, 0.8)'); // Green for on time
            else colors.push('rgba(23, 162, 184, 0.8)');                   // Blue for early
        }

        this.delayChart = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: labels,
                datasets: [{
                    label: 'Average Delay (minutes)',
                    data: data,
                    backgroundColor: colors,
                    borderColor: colors.map(color => color.replace('0.8', '1')),
                    borderWidth: 1
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    y: {
                        beginAtZero: true,
                        title: {
                            display: true,
                            text: 'Minutes'
                        }
                    },
                    x: {
                        title: {
                            display: true,
                            text: 'Hour of Day'
                        }
                    }
                },
                plugins: {
                    legend: {
                        display: false
                    },
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                const value = context.raw;
                                return `Average delay: ${value.toFixed(1)} minutes`;
                            }
                        }
                    }
                }
            }
        });
    }
}

// Initialize when page loads
document.addEventListener('DOMContentLoaded', () => {
    new StationDetailView();
});