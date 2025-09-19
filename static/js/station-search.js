class StationSearch {
    constructor() {
        this.searchInput = document.getElementById('stationSearch');
        this.searchResults = document.getElementById('searchResults');
        this.clearButton = document.getElementById('clearSearch');
        this.findNearbyButton = document.getElementById('findNearby');
        this.nearbyResults = document.getElementById('nearbyResults');
        this.systemStats = document.getElementById('systemStats');

        this.searchTimeout = null;

        this.initEventListeners();
        this.loadSystemStats();
    }

    initEventListeners() {
        // Search input with debouncing
        this.searchInput.addEventListener('input', () => {
            clearTimeout(this.searchTimeout);
            const query = this.searchInput.value.trim();

            if (query.length >= 2) {
                this.searchTimeout = setTimeout(() => {
                    this.searchStations(query);
                }, 300);
            } else {
                this.hideSearchResults();
            }
        });

        // Clear search
        this.clearButton.addEventListener('click', () => {
            this.searchInput.value = '';
            this.hideSearchResults();
            this.searchInput.focus();
        });

        // Find nearby stations
        this.findNearbyButton.addEventListener('click', () => {
            this.findNearbyStations();
        });

        // Hide search results when clicking outside
        document.addEventListener('click', (e) => {
            if (!this.searchInput.contains(e.target) && !this.searchResults.contains(e.target)) {
                this.hideSearchResults();
            }
        });
    }

    async searchStations(query) {
        try {
            const response = await fetch(`/api/stations/search?q=${encodeURIComponent(query)}&limit=10`);
            const stations = await response.json();

            this.displaySearchResults(stations);
        } catch (error) {
            console.error('Search error:', error);
            this.showError('Failed to search stations');
        }
    }

    displaySearchResults(stations) {
        if (stations.length === 0) {
            this.searchResults.innerHTML = '<div class="list-group-item">No stations found</div>';
        } else {
            this.searchResults.innerHTML = stations.map(station => `
                <div class="list-group-item list-group-item-action" data-station-id="${station.stop_id}">
                    <div class="d-flex justify-content-between align-items-center">
                        <div>
                            <h6 class="mb-1">${station.stop_name}</h6>
                            <small class="text-muted">ID: ${station.stop_id}</small>
                            ${station.stop_code ? `<span class="badge bg-secondary ms-2">${station.stop_code}</span>` : ''}
                        </div>
                        <i class="bi bi-arrow-right"></i>
                    </div>
                </div>
            `).join('');

            // Add click listeners to results
            this.searchResults.querySelectorAll('.list-group-item-action').forEach(item => {
                item.addEventListener('click', () => {
                    const stationId = item.dataset.stationId;
                    this.showStationDetails(stationId);
                });
            });
        }

        this.showSearchResults();
    }

    async findNearbyStations() {
        if (!navigator.geolocation) {
            this.showError('Geolocation is not supported by this browser');
            return;
        }

        this.findNearbyButton.innerHTML = '<i class="bi bi-arrow-clockwise spin"></i> Finding...';
        this.findNearbyButton.disabled = true;

        navigator.geolocation.getCurrentPosition(
            async (position) => {
                try {
                    const { latitude, longitude } = position.coords;
                    const response = await fetch(
                        `/api/stations/nearby?lat=${latitude}&lon=${longitude}&radius=1000`
                    );
                    const stations = await response.json();

                    this.displayNearbyResults(stations);
                } catch (error) {
                    console.error('Nearby search error:', error);
                    this.showError('Failed to find nearby stations');
                } finally {
                    this.findNearbyButton.innerHTML = '<i class="bi bi-geo-alt"></i> Use My Location';
                    this.findNearbyButton.disabled = false;
                }
            },
            (error) => {
                console.error('Geolocation error:', error);
                this.showError('Unable to get your location');
                this.findNearbyButton.innerHTML = '<i class="bi bi-geo-alt"></i> Use My Location';
                this.findNearbyButton.disabled = false;
            }
        );
    }

    displayNearbyResults(stations) {
        if (stations.length === 0) {
            this.nearbyResults.innerHTML = '<div class="list-group-item">No nearby stations found</div>';
        } else {
            this.nearbyResults.innerHTML = stations.map(station => `
                <div class="list-group-item list-group-item-action" data-station-id="${station.stop_id}">
                    <div class="d-flex justify-content-between align-items-center">
                        <div>
                            <h6 class="mb-1">${station.stop_name}</h6>
                            <small class="text-muted">
                                ${Math.round(station.distance)}m away
                                ${station.stop_code ? `• Code: ${station.stop_code}` : ''}
                            </small>
                        </div>
                        <i class="bi bi-arrow-right"></i>
                    </div>
                </div>
            `).join('');

            // Add click listeners
            this.nearbyResults.querySelectorAll('.list-group-item-action').forEach(item => {
                item.addEventListener('click', () => {
                    const stationId = item.dataset.stationId;
                    this.showStationDetails(stationId);
                });
            });
        }
    }

    async showStationDetails(stationId) {
        const modal = new bootstrap.Modal(document.getElementById('stationModal'));
        const modalTitle = document.getElementById('stationModalTitle');
        const modalBody = document.getElementById('stationModalBody');
        const viewDetailLink = document.getElementById('viewStationDetail');

        modalTitle.textContent = 'Loading...';
        modalBody.innerHTML = '<div class="text-center"><div class="spinner-border" role="status"></div></div>';
        viewDetailLink.href = `/station/${stationId}`;

        modal.show();

        try {
            const response = await fetch(`/api/station/${stationId}/delays?hours=24`);
            const data = await response.json();

            modalTitle.textContent = data.delays.length > 0 ?
                data.delays[0].stop_name || `Station ${stationId}` :
                `Station ${stationId}`;

            this.renderStationModal(data, modalBody);
        } catch (error) {
            console.error('Station details error:', error);
            modalBody.innerHTML = '<div class="alert alert-danger">Failed to load station details</div>';
        }
    }

    renderStationModal(data, container) {
        const { delays, stats } = data;

        if (stats.length === 0) {
            container.innerHTML = '<div class="alert alert-info">No delay data available for this station.</div>';
            return;
        }

        let html = '<div class="row">';

        // Route statistics
        html += '<div class="col-md-6"><h6>Route Statistics (24h)</h6>';
        stats.forEach(stat => {
            const onTimePercent = Math.round((stat.total_arrivals - stat.late_arrivals - stat.early_arrivals) / stat.total_arrivals * 100);
            const avgDelayMin = Math.round(stat.avg_delay / 60);
            html += `
                <div class="card mb-2">
                    <div class="card-body p-2">
                        <div class="d-flex justify-content-between align-items-center">
                            <span class="route-badge">${stat.route_short_name || stat.route_id}</span>
                            <div class="text-end">
                                <small class="text-muted">${stat.total_arrivals} arrivals</small><br>
                                <small class="delay-${avgDelayMin > 0 ? 'positive' : avgDelayMin < 0 ? 'negative' : 'neutral'}">
                                    ${avgDelayMin > 0 ? '+' : ''}${avgDelayMin}min avg
                                </small>
                            </div>
                        </div>
                        <div class="progress" style="height: 4px;">
                            <div class="progress-bar bg-success" style="width: ${onTimePercent}%"></div>
                        </div>
                        <small class="text-muted">${onTimePercent}% on time</small>
                    </div>
                </div>
            `;
        });
        html += '</div>';

        // Recent delays
        html += '<div class="col-md-6"><h6>Recent Arrivals</h6>';
        if (delays.length > 0) {
            html += '<div style="max-height: 300px; overflow-y: auto;">';
            delays.slice(0, 10).forEach(delay => {
                const delayMin = Math.round(delay.delay_seconds / 60);
                const arrivalTime = new Date(delay.actual_arrival_time).toLocaleTimeString();
                html += `
                    <div class="d-flex justify-content-between align-items-center mb-2 p-2 bg-light rounded">
                        <div>
                            <span class="route-badge">${delay.route_short_name || delay.route_id}</span>
                            <small class="text-muted">${arrivalTime}</small>
                        </div>
                        <span class="delay-${delayMin > 0 ? 'positive' : delayMin < 0 ? 'negative' : 'neutral'}">
                            ${delayMin > 0 ? '+' : ''}${delayMin}min
                        </span>
                    </div>
                `;
            });
            html += '</div>';
        } else {
            html += '<div class="alert alert-info">No recent delay data available.</div>';
        }
        html += '</div></div>';

        container.innerHTML = html;
    }

    async loadSystemStats() {
        try {
            const response = await fetch('/api/analytics/system-stats');
            const stats = await response.json();

            const formatNumber = (num) => {
                if (num >= 1000000) return (num / 1000000).toFixed(1) + 'M';
                if (num >= 1000) return (num / 1000).toFixed(1) + 'K';
                return num.toString();
            };

            const lastUpdate = stats.latest_update ?
                new Date(stats.latest_update).toLocaleString() : 'Unknown';

            this.systemStats.innerHTML = `
                <div class="row text-center">
                    <div class="col-6 mb-2">
                        <strong class="text-primary">${formatNumber(stats.total_records)}</strong><br>
                        <small class="text-muted">Total Records</small>
                    </div>
                    <div class="col-6 mb-2">
                        <strong class="text-success">${stats.unique_routes}</strong><br>
                        <small class="text-muted">Routes</small>
                    </div>
                    <div class="col-6 mb-2">
                        <strong class="text-warning">${formatNumber(stats.recent_records)}</strong><br>
                        <small class="text-muted">Last 24h</small>
                    </div>
                    <div class="col-6 mb-2">
                        <strong class="text-info">${formatNumber(stats.recent_delays)}</strong><br>
                        <small class="text-muted">Recent Delays</small>
                    </div>
                </div>
                <hr>
                <small class="text-muted">Last update: ${lastUpdate}</small>
            `;
        } catch (error) {
            console.error('System stats error:', error);
            this.systemStats.innerHTML = '<div class="alert alert-warning">Unable to load system stats</div>';
        }
    }

    showSearchResults() {
        this.searchResults.style.display = 'block';
    }

    hideSearchResults() {
        this.searchResults.style.display = 'none';
    }

    showError(message) {
        // You could implement a toast notification here
        console.error(message);
    }
}

// Initialize when page loads
document.addEventListener('DOMContentLoaded', () => {
    new StationSearch();
});

// Add spinning animation for loading buttons
const style = document.createElement('style');
style.textContent = `
    @keyframes spin {
        from { transform: rotate(0deg); }
        to { transform: rotate(360deg); }
    }
    .spin { animation: spin 1s linear infinite; }
`;
document.head.appendChild(style);