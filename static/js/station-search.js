class StationSearch {
    constructor() {
        this.searchInput = document.getElementById('stationSearch');
        this.searchResults = document.getElementById('searchResults');
        this.clearButton = document.getElementById('clearSearch');
        this.findNearbyButton = document.getElementById('findNearby');
        this.nearbyResults = document.getElementById('nearbyResults');
        this.stationDetails = document.getElementById('stationDetails');

        this.searchTimeout = null;

        this.initEventListeners();
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
            this.showError('Gat ekki leitað að stöðvum');
        }
    }

    displaySearchResults(stations) {
        if (stations.length === 0) {
            this.searchResults.innerHTML = '<div class="result-item">Engar stöðvar fundust</div>';
        } else {
            this.searchResults.innerHTML = stations.map(station => `
                <div class="result-item" data-station-name="${station.stop_name}">
                    <div class="d-flex justify-content-between align-items-center">
                        <div>
                            <h6 class="mb-1">${station.stop_name}</h6>
                            <small class="text-muted">${station.station_count} stöðvar</small>
                        </div>
                        <i class="bi bi-arrow-right"></i>
                    </div>
                </div>
            `).join('');

            // Add click listeners to results
            this.searchResults.querySelectorAll('.result-item').forEach(item => {
                item.addEventListener('click', () => {
                    const stationName = item.dataset.stationName;
                    this.showStationNameDetails(stationName);
                });
            });
        }

        this.showSearchResults();
    }

    async findNearbyStations() {
        if (!navigator.geolocation) {
            this.showError('Staðsetning er ekki studd í þessum vafra');
            return;
        }

        this.findNearbyButton.innerHTML = `<i class="bi bi-arrow-clockwise spin"></i> ${t('SEARCHING')}`;
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
                    this.showError(t('ERROR_FIND_NEARBY'));
                } finally {
                    this.findNearbyButton.innerHTML = `<i class="bi bi-geo-alt"></i> ${t('USE_MY_LOCATION')}`;
                    this.findNearbyButton.disabled = false;
                }
            },
            (error) => {
                console.error('Geolocation error:', error);
                this.showError(t('ERROR_GET_LOCATION'));
                this.findNearbyButton.innerHTML = '<i class="bi bi-geo-alt"></i> Use My Location';
                this.findNearbyButton.disabled = false;
            }
        );
    }

    displayNearbyResults(stations) {
        if (stations.length === 0) {
            this.nearbyResults.innerHTML = `<div class="result-item">${t('NO_NEARBY_STATIONS')}</div>`;
        } else {
            this.nearbyResults.innerHTML = stations.map(station => `
                <div class="result-item" data-station-id="${station.stop_id}">
                    <div class="d-flex justify-content-between align-items-center">
                        <div>
                            <h6 class="mb-1">${station.stop_name}</h6>
                            <small class="text-muted">
                                ${Math.round(station.distance)}m í burtu
                                ${station.stop_code ? `• Kóði: ${station.stop_code}` : ''}
                            </small>
                        </div>
                        <i class="bi bi-arrow-right"></i>
                    </div>
                </div>
            `).join('');

            // Add click listeners
            this.nearbyResults.querySelectorAll('.result-item').forEach(item => {
                item.addEventListener('click', () => {
                    const stationId = item.dataset.stationId;
                    this.showStationDetails(stationId);
                });
            });
        }

        this.nearbyResults.style.display = 'block';
    }

    async showStationNameDetails(stationName) {
        // Hide other results
        this.hideSearchResults();
        this.nearbyResults.style.display = 'none';

        // Show loading state
        this.stationDetails.innerHTML = `
            <div class="result-item">
                <h5>${stationName}</h5>
                <div class="text-center">
                    <div class="spinner-border" role="status">
                        <span class="visually-hidden">${t('LOADING')}</span>
                    </div>
                </div>
            </div>
        `;
        this.stationDetails.style.display = 'block';

        try {
            const response = await fetch(`/api/station-name/${encodeURIComponent(stationName)}/buses`);
            const data = await response.json();

            if (data.error) {
                this.stationDetails.innerHTML = `
                    <div class="result-item">
                        <h5>${stationName}</h5>
                        <div class="alert alert-danger">${data.error}</div>
                    </div>
                `;
                return;
            }

            this.renderStationNameDetails(data);
        } catch (error) {
            console.error('Station details error:', error);
            this.stationDetails.innerHTML = `
                <div class="result-item">
                    <h5>${stationName}</h5>
                    <div class="alert alert-danger">${t('ERROR_LOAD_STATION_DETAILS')}</div>
                </div>
            `;
        }
    }

    async showStationDetails(stationId) {
        const modal = new bootstrap.Modal(document.getElementById('stationModal'));
        const modalTitle = document.getElementById('stationModalTitle');
        const modalBody = document.getElementById('stationModalBody');
        const viewDetailLink = document.getElementById('viewStationDetail');

        modalTitle.textContent = 'Hleður...';
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
            modalBody.innerHTML = '<div class="alert alert-danger">Gat ekki hlaðið upplýsingar um stöð</div>';
        }
    }

    renderStationNameDetails(data) {
        const { station_name, stations, approaching_buses } = data;

        if (approaching_buses.length === 0) {
            this.stationDetails.innerHTML = `
                <div class="result-item">
                    <h5>${station_name}</h5>
                    <div class="alert alert-info">${t('NO_DATA_AVAILABLE')}</div>
                </div>
            `;
            return;
        }

        let html = `
            <div class="result-item">
                <h5>${station_name}</h5>
                <small class="text-muted">${stations.length} ${stations.length === 1 ? 'stöð' : 'stöðvar'} með þessu nafni</small>
                <h6 class="mt-3">${t('APPROACHING_BUSES')}</h6>
            </div>
        `;

        approaching_buses.forEach(bus => {
            const delayMin = Math.round((bus.latest_delay_seconds || 0) / 60);
            const delayClass = delayMin > 0 ? 'positive' : delayMin < 0 ? 'negative' : 'neutral';

            html += `
                <div class="result-item">
                    <div class="d-flex justify-content-between align-items-center">
                        <div>
                            <span class="route-badge">${bus.route_short_name || bus.route_id}</span>
                            <small class="text-muted ms-2">${bus.route_long_name || ''}</small>
                        </div>
                        <div class="text-end">
                            <div class="delay-${delayClass}">
                                ${delayMin > 0 ? '+' : ''}${delayMin} ${t('MINUTES_ABBREV')}
                            </div>
                            <small class="text-muted">
                                ${bus.bus_status.speed_kmh ? `${Math.round(bus.bus_status.speed_kmh)} km/h` : ''}
                            </small>
                        </div>
                    </div>
                </div>
            `;
        });

        this.stationDetails.innerHTML = html;
    }

    renderStationModal(data, container) {
        const { delays, stats } = data;

        if (stats.length === 0) {
            container.innerHTML = '<div class="alert alert-info">Engin töfugjögn til staðar fyrir þessa stöð.</div>';
            return;
        }

        let html = '<div class="row">';

        // Route statistics
        html += '<div class="col-md-6"><h6>Leiðartölfræði (24 klst)</h6>';
        stats.forEach(stat => {
            const onTimePercent = Math.round((stat.total_arrivals - stat.late_arrivals - stat.early_arrivals) / stat.total_arrivals * 100);
            const avgDelayMin = Math.round(stat.avg_delay / 60);
            html += `
                <div class="card mb-2">
                    <div class="card-body p-2">
                        <div class="d-flex justify-content-between align-items-center">
                            <span class="route-badge">${stat.route_short_name || stat.route_id}</span>
                            <div class="text-end">
                                <small class="text-muted">${stat.total_arrivals} komur</small><br>
                                <small class="delay-${avgDelayMin > 0 ? 'positive' : avgDelayMin < 0 ? 'negative' : 'neutral'}">
                                    ${avgDelayMin > 0 ? '+' : ''}${avgDelayMin} mín meðal
                                </small>
                            </div>
                        </div>
                        <div class="progress" style="height: 4px;">
                            <div class="progress-bar bg-success" style="width: ${onTimePercent}%"></div>
                        </div>
                        <small class="text-muted">${onTimePercent}% á réttum tíma</small>
                    </div>
                </div>
            `;
        });
        html += '</div>';

        // Recent delays
        html += '<div class="col-md-6"><h6>Nýlegar komur</h6>';
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
                            ${delayMin > 0 ? '+' : ''}${delayMin} mín
                        </span>
                    </div>
                `;
            });
            html += '</div>';
        } else {
            html += '<div class="alert alert-info">Engin nýleg töfugjögn til staðar.</div>';
        }
        html += '</div></div>';

        container.innerHTML = html;
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