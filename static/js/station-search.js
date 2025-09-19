class StationSearch {
    constructor() {
        this.searchInput = document.getElementById('stationSearch');
        this.searchResults = document.getElementById('searchResults');
        this.findNearbyButton = document.getElementById('findNearby');
        this.nearbyResults = document.getElementById('nearbyResults');
        this.stationDetails = document.getElementById('stationDetails');
        this.busMap = document.getElementById('busMap');
        this.mapContainer = document.getElementById('mapContainer');

        this.searchTimeout = null;
        this.map = null;
        this.mapMarkers = [];

        // Auto-refresh functionality
        this.refreshInterval = null;
        this.refreshKillswitch = null;
        this.currentStationName = null;
        this.lastBusData = null;
        this.isRefreshing = false;

        // Route color mapping from route-colors.css
        this.routeColors = {
            'S1': { color: '#fff', text: '#11b09b' },
            'S-song': { color: '#e129f1', text: '#fff' },
            'S-pride': { color: '#ef3026', text: '#fff' }, // Using first color of gradient
            '1': { color: '#ef4934', text: '#fff' },
            '2': { color: '#acc437', text: '#000' },
            '3': { color: '#fdbc14', text: '#000' },
            '4': { color: '#306e4a', text: '#fff' },
            '5': { color: '#db1a5a', text: '#fff' },
            '6': { color: '#00a754', text: '#fff' },
            '7': { color: '#cb4138', text: '#fff' },
            '8': { color: '#11b09b', text: '#fff' },
            '11': { color: '#e35289', text: '#fff' },
            '12': { color: '#0a68b3', text: '#fff' },
            '13': { color: '#00a2b5', text: '#fff' },
            '14': { color: '#7157a4', text: '#fff' },
            '15': { color: '#215266', text: '#fff' },
            '16': { color: '#d9c127', text: '#000' },
            '17': { color: '#564b1e', text: '#fff' },
            '18': { color: '#f26c4e', text: '#fff' },
            '19': { color: '#589b55', text: '#fff' },
            '21': { color: '#e0b33c', text: '#000' },
            '22': { color: '#00a97d', text: '#fff' },
            '23': { color: '#292565', text: '#fff' },
            '24': { color: '#26566c', text: '#fff' },
            '25': { color: '#2491d3', text: '#fff' },
            '26': { color: '#0a68b3', text: '#fff' },
            '27': { color: '#69ba9b', text: '#fff' },
            '28': { color: '#bd107d', text: '#fff' },
            '29': { color: '#494845', text: '#fff' },
            '31': { color: '#6b5661', text: '#fff' },
            '33': { color: '#cc8d3d', text: '#fff' },
            '34': { color: '#98c568', text: '#fff' },
            '35': { color: '#206574', text: '#fff' },
            '36': { color: '#f18b28', text: '#fff' },
            '43': { color: '#847b5a', text: '#fff' },
            '44': { color: '#2d2c7e', text: '#fff' },
            '51': { color: '#bd107d', text: '#fff' },
            '52': { color: '#4578ac', text: '#fff' },
            '55': { color: '#4578ac', text: '#fff' },
            '56': { color: '#2f2b7f', text: '#fff' },
            '57': { color: '#e53c2e', text: '#fff' },
            '58': { color: '#68bb95', text: '#fff' },
            '59': { color: '#295468', text: '#fff' },
            '61': { color: '#47105f', text: '#fff' },
            '62': { color: '#9b2e2a', text: '#fff' },
            '63': { color: '#744f98', text: '#fff' },
            '64': { color: '#0a9d0a', text: '#fff' },
            '65': { color: '#febc10', text: '#000' },
            '71': { color: '#2d6d46', text: '#fff' },
            '72': { color: '#b3c338', text: '#000' },
            '73': { color: '#eb654b', text: '#fff' },
            '75': { color: '#575454', text: '#fff' },
            '78': { color: '#18a7bc', text: '#fff' },
            '79': { color: '#f08728', text: '#fff' },
            '81': { color: '#827b55', text: '#fff' },
            '82': { color: '#de4c84', text: '#fff' },
            '83': { color: '#ddc030', text: '#000' },
            '84': { color: '#f36f20', text: '#fff' },
            '87': { color: '#fbbd2b', text: '#000' },
            '88': { color: '#d60e51', text: '#fff' },
            '89': { color: '#199d48', text: '#fff' },
            '91': { color: '#ef4934', text: '#fff' },
            '92': { color: '#00a754', text: '#fff' },
            '93': { color: '#fdbc14', text: '#000' },
            '94': { color: '#7157a4', text: '#fff' },
            '95': { color: '#0a68b3', text: '#fff' },
            '96': { color: '#f59c27', text: '#000' },
            '101': { color: '#d22328', text: '#fff' },
            '102': { color: '#0a9d0a', text: '#fff' },
            '103': { color: '#e8b42e', text: '#fff' },
            '104': { color: '#068cfd', text: '#fff' },
            '105': { color: '#d22328', text: '#fff' },
            '106': { color: '#db654f', text: '#fff' },
            '107': { color: '#d11ec8', text: '#fff' },
            'A1': { color: '#0a68b3', text: '#fff' },
            'A2': { color: '#ef4934', text: '#fff' },
            'A3': { color: '#00a2b5', text: '#fff' },
            'A4': { color: '#f26c4e', text: '#fff' },
            'A5': { color: '#00a754', text: '#fff' },
            'A6': { color: '#7157a4', text: '#fff' },
            'R1': { color: '#0a68b3', text: '#fff' },
            'R2': { color: '#fdbc14', text: '#000' },
            'R3': { color: '#fdbc14', text: '#000' },
            'R4': { color: '#ef4934', text: '#fff' },
            'E1': { color: '#ef4934', text: '#fff' },
            'E2': { color: '#00a754', text: '#fff' },
            'E3': { color: '#fdbc14', text: '#000' },
            'E4': { color: '#7157a4', text: '#fff' },
            'E5': { color: '#0a68b3', text: '#fff' }
        };

        this.initEventListeners();
    }

    initEventListeners() {
        // Search input with debouncing
        this.searchInput.addEventListener('input', () => {
            clearTimeout(this.searchTimeout);
            const query = this.searchInput.value.trim();

            // Stop auto-refresh when starting a new search
            if (query.length >= 2) {
                this.stopAutoRefresh();
                this.searchTimeout = setTimeout(() => {
                    this.searchStations(query);
                }, 300);
            } else {
                this.hideSearchResults();
            }
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

        // Stop refresh when page is hidden or user navigates away
        document.addEventListener('visibilitychange', () => {
            if (document.hidden) {
                this.stopAutoRefresh();
            }
        });

        window.addEventListener('beforeunload', () => {
            this.stopAutoRefresh();
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
            this.searchResults.innerHTML = `<div class="result-item">${t('NO_STATIONS_FOUND') || 'Engar stöðvar fundust'}</div>`;
        } else {
            this.searchResults.innerHTML = stations.map(station => `
                <div class="result-item" data-station-name="${station.stop_name}">
                    <div class="d-flex justify-content-between align-items-center">
                        <div>
                            <h6 class="mb-1">${station.stop_name}</h6>
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

        this.findNearbyButton.innerHTML = `<i class="bi bi-arrow-clockwise spin"></i>`;
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
                    this.findNearbyButton.innerHTML = `<i class="bi bi-geo-alt"></i>`;
                    this.findNearbyButton.disabled = false;
                }
            },
            (error) => {
                console.error('Geolocation error:', error);
                this.showError(t('ERROR_GET_LOCATION'));
                this.findNearbyButton.innerHTML = '<i class="bi bi-geo-alt"></i>';
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
                                ${Math.round(station.distance)}m ${t('METERS_AWAY')}
                                ${station.stop_code ? `• ${t('CODE_LABEL')} ${station.stop_code}` : ''}
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
        // Stop any existing refresh
        this.stopAutoRefresh();

        // Hide other results
        this.hideSearchResults();
        this.nearbyResults.style.display = 'none';
        this.hideMap();

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

            // Start auto-refresh for this station
            this.startAutoRefresh(stationName);

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
        const { station_name, stations, approaching_buses, stations_count } = data;

        if (approaching_buses.length === 0) {
            this.stationDetails.innerHTML = `
                <div class="result-item">
                    <h5>${station_name}</h5>
                    <div class="alert alert-info mt-3">${t('NO_BUSES_APPROACHING')}</div>
                </div>
            `;
            this.hideMap();
            return;
        }

        // Group buses by station
        const busesByStation = {};
        approaching_buses.forEach(bus => {
            const stationId = bus.station_id;
            if (!busesByStation[stationId]) {
                busesByStation[stationId] = {
                    station: stations.find(s => s.stop_id === stationId),
                    buses: []
                };
            }
            busesByStation[stationId].buses.push(bus);
        });

        let html = `
            <div class="result-item">
                <h5>${station_name}</h5>
            </div>
        `;

        // Assign A/B labels if multiple stations
        const stationEntries = Object.values(busesByStation);
        const stationLabels = stationEntries.length > 1 ? ['A', 'B'] : [''];

        // Render each station separately - only show closest bus per route
        stationEntries.forEach((stationData, index) => {
            const station = stationData.station;
            const buses = stationData.buses;
            const label = stationLabels[index] || '';

            html += `
                <div class="result-item">
                    <div class="d-flex justify-content-between align-items-center mb-2">
                        <h6 class="mb-0">${station.stop_name}${label ? ` ${label}` : ''}</h6>
                    </div>
            `;

            if (buses.length === 0) {
                html += `<div class="text-muted">${t('NO_BUSES_FOR_STATION')}</div>`;
            } else {
                // Group buses by route and show only the closest one
                const closestByRoute = {};
                buses.forEach(bus => {
                    const routeKey = bus.route || 'Unknown';
                    if (!closestByRoute[routeKey] || bus.stops_away < closestByRoute[routeKey].stops_away) {
                        closestByRoute[routeKey] = bus;
                    }
                });

                Object.values(closestByRoute).forEach(bus => {
                    // Format stops away text - check if bus is currently at this station
                    let stopsAwayText;
                    if (bus.stop_id === station.stop_id) {
                        // Bus is at the station according to stop_id, but check distance
                        if (bus.latitude && bus.longitude && station.stop_lat && station.stop_lon) {
                            const distance = this.calculateDistance(
                                bus.latitude, bus.longitude,
                                station.stop_lat, station.stop_lon
                            );

                            if (distance > 50) {
                                stopsAwayText = t('LEAVING_STATION');
                            } else {
                                stopsAwayText = t('AT_STATION');
                            }
                        } else {
                            stopsAwayText = t('AT_STATION');
                        }
                    } else if (bus.stops_away === 0) {
                        stopsAwayText = t('NEXT_STOP_IS_HERE');
                    } else if (bus.stops_away === 1) {
                        stopsAwayText = `1 ${t('STOPS_AWAY_SINGLE')}`;
                    } else {
                        stopsAwayText = `${bus.stops_away} ${t('STOPS_AWAY_PLURAL')}`;
                    }

                    // Format delay information for detailed text
                    let delayInfoText = '';
                    if (bus.delay_seconds !== null && bus.delay_seconds !== undefined) {
                        // Use 30 second cutoff for "on time"
                        if (Math.abs(bus.delay_seconds) <= 30) {
                            delayInfoText = t('DELAY_INFO_TEMPLATE')
                                .replace('{time}', '')
                                .replace('{status}', t('DELAY_STATUS_ON_TIME'))
                                .replace('Var  ', 'Var '); // Clean up double space
                        } else {
                            const minutes = Math.floor(Math.abs(bus.delay_seconds) / 60);
                            const seconds = Math.abs(bus.delay_seconds) % 60;
                            const timeFormat = `${minutes}:${seconds.toString().padStart(2, '0')}`;

                            let statusKey = bus.delay_seconds > 0 ? 'DELAY_STATUS_LATE' : 'DELAY_STATUS_EARLY';

                            delayInfoText = t('DELAY_INFO_TEMPLATE')
                                .replace('{time}', timeFormat)
                                .replace('{status}', t(statusKey));
                        }
                    }

                    // Get route colors
                    const routeColors = this.routeColors[bus.route] || { color: '#B2272D', text: '#fff' };

                    // Format scheduled departure time if available
                    let scheduledDeparture = '';
                    if (bus.scheduled_departure_time) {
                        const time = bus.scheduled_departure_time.substring(0, 5); // Get HH:MM format
                        scheduledDeparture = `<span style="color: #888; font-size: 0.85em; margin-left: 8px;">@${time}</span>`;
                    }

                    html += `
                        <div class="bus-item mb-2 p-2 border rounded">
                            <div class="d-flex justify-content-between align-items-start">
                                <div class="flex-grow-1">
                                    <div class="mb-1 d-flex align-items-center">
                                        <span class="route-badge" style="background-color: ${routeColors.color}; color: ${routeColors.text}; border-radius: 50%; width: 32px; height: 32px; display: inline-flex; align-items: center; justify-content: center; font-weight: bold; font-size: 12px;">${bus.route || 'N/A'}</span>
                                        ${bus.trip_headsign ? `<span style="margin-left: 8px; font-weight: bold; font-size: 1.1em;">${bus.trip_headsign}</span>` : ''}
                                        ${scheduledDeparture}
                                    </div>
                                    <div style="color: black; font-size: 0.9em;">
                                        ${stopsAwayText}. ${delayInfoText}
                                    </div>
                                </div>
                            </div>
                        </div>
                    `;
                });
            }

            html += '</div>';
        });

        this.stationDetails.innerHTML = html;

        // Show map with all buses and stations (this is a new station load)
        this.showMap(stations, approaching_buses, true);
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
            const routeColors = this.routeColors[stat.route_short_name || stat.route_id] || { color: '#B2272D', text: '#fff' };
            html += `
                <div class="card mb-2">
                    <div class="card-body p-2">
                        <div class="d-flex justify-content-between align-items-center">
                            <span class="route-badge" style="background-color: ${routeColors.color}; color: ${routeColors.text}; border-radius: 50%; width: 32px; height: 32px; display: inline-flex; align-items: center; justify-content: center; font-weight: bold; font-size: 12px;">${stat.route_short_name || stat.route_id}</span>
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
                const routeColors = this.routeColors[delay.route_short_name || delay.route_id] || { color: '#B2272D', text: '#fff' };
                html += `
                    <div class="d-flex justify-content-between align-items-center mb-2 p-2 bg-light rounded">
                        <div>
                            <span class="route-badge" style="background-color: ${routeColors.color}; color: ${routeColors.text}; border-radius: 50%; width: 24px; height: 24px; display: inline-flex; align-items: center; justify-content: center; font-weight: bold; font-size: 10px; margin-right: 8px;">${delay.route_short_name || delay.route_id}</span>
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

    hideStationDetails() {
        this.stationDetails.style.display = 'none';
        this.stopAutoRefresh();
    }

    showError(message) {
        // You could implement a toast notification here
        console.error(message);
    }

    calculateDistance(lat1, lon1, lat2, lon2) {
        // Haversine formula to calculate distance in meters
        const R = 6371000; // Earth's radius in meters
        const dLat = (lat2 - lat1) * Math.PI / 180;
        const dLon = (lon2 - lon1) * Math.PI / 180;
        const a = Math.sin(dLat/2) * Math.sin(dLat/2) +
                  Math.cos(lat1 * Math.PI / 180) * Math.cos(lat2 * Math.PI / 180) *
                  Math.sin(dLon/2) * Math.sin(dLon/2);
        const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1-a));
        return R * c;
    }

    showMap(stations, buses, isNewStation = false) {
        this.busMap.style.display = 'block';

        let shouldFitBounds = false;

        // Initialize map if not already done
        if (!this.map) {
            this.map = L.map(this.mapContainer).setView([64.1466, -21.9426], 12);
            L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
                attribution: '© OpenStreetMap contributors'
            }).addTo(this.map);
            shouldFitBounds = true;
        }

        // Store current map view if this is a refresh
        const currentCenter = this.map.getCenter();
        const currentZoom = this.map.getZoom();
        const isRefresh = this.mapMarkers.length > 0 && !isNewStation;

        // Clear existing markers
        this.clearMapMarkers();

        // Add station markers with A/B labels if multiple stations
        const stationLabels = stations.length > 1 ? ['A', 'B'] : [''];

        stations.forEach((station, index) => {
            if (station.stop_lat && station.stop_lon) {
                const label = stationLabels[index] || '';

                const stationIcon = L.divIcon({
                    className: 'station-marker',
                    html: label ?
                        `<div class="station-label" style="background: white; border: 2px solid #B2272D; border-radius: 50%; width: 24px; height: 24px; display: flex; align-items: center; justify-content: center; font-weight: bold; font-size: 14px; color: #B2272D; box-shadow: 0 2px 4px rgba(0,0,0,0.2);">
                            ${label}
                        </div>` :
                        `<div class="station-dot" style="background: #B2272D; border: 2px solid white; border-radius: 50%; width: 12px; height: 12px; box-shadow: 0 2px 4px rgba(0,0,0,0.3);">
                        </div>`,
                    iconSize: [24, 24],
                    iconAnchor: [12, 12]
                });

                const marker = L.marker([station.stop_lat, station.stop_lon], { icon: stationIcon })
                    .bindPopup(`
                        <div>
                            <strong>${station.stop_name}${label ? ` ${label}` : ''}</strong><br>
                            ${station.stop_code ? `Code: ${station.stop_code}<br>` : ''}
                        </div>
                    `)
                    .addTo(this.map);

                this.mapMarkers.push(marker);
            }
        });

        // Add bus markers
        buses.forEach(bus => {
            if (bus.latitude && bus.longitude) {
                // Get route colors
                const routeColors = this.routeColors[bus.route] || { color: '#B2272D', text: '#fff' };

                const busIcon = L.divIcon({
                    className: 'bus-marker',
                    html: `<div class="bus-icon">
                        <div class="bus-route-badge" style="background-color: ${routeColors.color}; color: ${routeColors.text}; border-radius: 50%; width: 24px; height: 24px; display: flex; align-items: center; justify-content: center; font-weight: bold; font-size: 11px; box-shadow: 0 2px 4px rgba(0,0,0,0.2);">
                            ${bus.route}
                        </div>
                    </div>`,
                    iconSize: [24, 24],
                    iconAnchor: [12, 12]
                });

                // Check if bus is currently at any of the target stations
                let stopsAwayText;
                const matchingStation = stations.find(station => bus.stop_id === station.stop_id);

                if (matchingStation) {
                    // Bus is at a target station according to stop_id, but check distance
                    if (bus.latitude && bus.longitude && matchingStation.stop_lat && matchingStation.stop_lon) {
                        const distance = this.calculateDistance(
                            bus.latitude, bus.longitude,
                            matchingStation.stop_lat, matchingStation.stop_lon
                        );

                        if (distance > 50) {
                            stopsAwayText = t('LEAVING_STATION');
                        } else {
                            stopsAwayText = t('AT_STATION');
                        }
                    } else {
                        stopsAwayText = t('AT_STATION');
                    }
                } else if (bus.stops_away === 0) {
                    stopsAwayText = t('NEXT_STOP_IS_HERE');
                } else if (bus.stops_away === 1) {
                    stopsAwayText = `1 ${t('STOPS_AWAY_SINGLE')}`;
                } else {
                    stopsAwayText = `${bus.stops_away} ${t('STOPS_AWAY_PLURAL')}`;
                }

                // Format delay information for popup
                let delayInfoText = '';
                if (bus.delay_seconds !== null && bus.delay_seconds !== undefined) {
                    // Use 30 second cutoff for "on time"
                    if (Math.abs(bus.delay_seconds) <= 30) {
                        delayInfoText = t('DELAY_INFO_TEMPLATE')
                            .replace('{time}', '')
                            .replace('{status}', t('DELAY_STATUS_ON_TIME'))
                            .replace('Var  ', 'Var '); // Clean up double space
                    } else {
                        const minutes = Math.floor(Math.abs(bus.delay_seconds) / 60);
                        const seconds = Math.abs(bus.delay_seconds) % 60;
                        const timeFormat = `${minutes}:${seconds.toString().padStart(2, '0')}`;

                        let statusKey = bus.delay_seconds > 0 ? 'DELAY_STATUS_LATE' : 'DELAY_STATUS_EARLY';

                        delayInfoText = t('DELAY_INFO_TEMPLATE')
                            .replace('{time}', timeFormat)
                            .replace('{status}', t(statusKey));
                    }
                }

                const marker = L.marker([bus.latitude, bus.longitude], { icon: busIcon })
                    .bindPopup(`
                        <div>
                            <strong>${t('ROUTE')}: ${bus.route}</strong>
                            ${bus.trip_headsign ? ` ${bus.trip_headsign}` : ''}<br>
                            <small style="color: black;">${stopsAwayText}. ${delayInfoText}</small>
                        </div>
                    `)
                    .addTo(this.map);

                this.mapMarkers.push(marker);
            }
        });

        // Fit bounds on initial load or when loading a new station, preserve view on refresh
        if ((shouldFitBounds || isNewStation) && this.mapMarkers.length > 0) {
            const group = new L.featureGroup(this.mapMarkers);
            this.map.fitBounds(group.getBounds().pad(0.1));
        } else if (isRefresh) {
            // Restore previous view for refresh
            this.map.setView(currentCenter, currentZoom);
        }

        // Force map resize after showing
        setTimeout(() => {
            this.map.invalidateSize();
        }, 100);
    }

    hideMap() {
        this.busMap.style.display = 'none';
        this.clearMapMarkers();
    }

    clearMapMarkers() {
        this.mapMarkers.forEach(marker => {
            this.map.removeLayer(marker);
        });
        this.mapMarkers = [];
    }

    startAutoRefresh(stationName) {
        this.stopAutoRefresh();
        this.currentStationName = stationName;

        // Set up 15-second refresh interval
        this.refreshInterval = setInterval(() => {
            if (!this.isRefreshing && this.currentStationName) {
                this.refreshStationData();
            }
        }, 15000);

        // Set up 5-minute killswitch
        this.refreshKillswitch = setTimeout(() => {
            this.stopAutoRefresh();
            console.log('Auto-refresh stopped after 5 minutes');
        }, 5 * 60 * 1000);
    }

    stopAutoRefresh() {
        if (this.refreshInterval) {
            clearInterval(this.refreshInterval);
            this.refreshInterval = null;
        }

        if (this.refreshKillswitch) {
            clearTimeout(this.refreshKillswitch);
            this.refreshKillswitch = null;
        }

        this.currentStationName = null;
        this.lastBusData = null;
        this.isRefreshing = false;
    }

    async refreshStationData() {
        if (!this.currentStationName || this.isRefreshing) {
            return;
        }

        this.isRefreshing = true;

        try {
            const response = await fetch(`/api/station-name/${encodeURIComponent(this.currentStationName)}/buses`);
            const data = await response.json();

            if (data.error) {
                console.error('Refresh error:', data.error);
                return;
            }

            // Update with minimal flicker
            this.updateStationDataWithMinimalFlicker(data);

        } catch (error) {
            console.error('Refresh error:', error);
        } finally {
            this.isRefreshing = false;
        }
    }

    updateStationDataWithMinimalFlicker(data) {
        const { station_name, stations, approaching_buses } = data;

        // Store current scroll position
        const scrollPosition = window.scrollY;

        // Check if we need to update (compare with last data)
        if (this.lastBusData && this.areBusDataEqual(this.lastBusData.approaching_buses, approaching_buses)) {
            return; // No changes, skip update
        }

        this.lastBusData = data;

        // Update station details without full re-render if possible
        this.renderStationNameDetails(data);

        // Restore scroll position
        window.scrollTo(0, scrollPosition);
    }

    areBusDataEqual(oldBuses, newBuses) {
        if (!oldBuses || !newBuses || oldBuses.length !== newBuses.length) {
            return false;
        }

        // Create a simple comparison based on key bus data
        const oldKey = oldBuses.map(bus =>
            `${bus.route}_${bus.trip_id}_${bus.stops_away}_${Math.floor((bus.delay_seconds || 0) / 30)}`
        ).sort().join('|');

        const newKey = newBuses.map(bus =>
            `${bus.route}_${bus.trip_id}_${bus.stops_away}_${Math.floor((bus.delay_seconds || 0) / 30)}`
        ).sort().join('|');

        return oldKey === newKey;
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