// Centralized translations for Strætó Monitor
// All user-facing text is collected here for easy translation and proofreading

const TRANSLATIONS = {
    EN: {
        // Application name and branding
        APP_NAME: "Strætó Monitor",

        // Navigation
        NAV_STATION_SEARCH: "Station Search",
        NAV_ANALYTICS: "Analytics",

        // Main page - Station search
        PAGE_TITLE_STATION_SEARCH: "Station Search - Strætó Monitor",
        STATION_SEARCH_TITLE: "Find Bus Station",
        MAIN_QUESTION: "Is the bus running late?",
        SEARCH_BY_NAME: "Search by name",
        SEARCH_PLACEHOLDER: "Enter station name...",
        FIND_NEARBY_STATIONS: "Find nearby stations",
        USE_MY_LOCATION: "Use my location",

        // How to use section
        HOW_TO_USE: "How to use",
        HOW_TO_SEARCH: "Search for stations by name or code",
        HOW_TO_LOCATION: "Find stations near your location",
        HOW_TO_DELAYS: "View real-time delay information",
        HOW_TO_ANALYTICS: "Check analytics for route performance",

        // System status
        SYSTEM_STATUS: "System Status",
        LOADING: "Loading...",
        CLOSE: "Close",
        VIEW_ALL_DETAILS: "View all details",

        // Analytics page
        PAGE_TITLE_ANALYTICS: "Analytics - Strætó Monitor",
        SYSTEM_ANALYTICS: "System Analytics",
        TOTAL_RECORDS: "Total Records",
        ACTIVE_ROUTES: "Active Routes",
        LAST_24H: "Last 24h",
        RECENT_DELAYS: "Recent Delays",

        // Station-route analysis
        WORST_STATION_ROUTE_PAIRS: "Worst Station-Route Pairs",
        MOST_DELAYED: "Most Delayed",
        MOST_EARLY: "Most Early",

        // Speed heatmap
        SPEED_HEATMAP: "Speed Heatmap",
        SPEED_KMH: "Speed (km/h)",
        ROUTE: "Route",
        SPEED: "Speed",

        // Route performance
        ROUTE_PERFORMANCE: "Route Performance",
        ON_TIME: "On Time",
        LATE: "Late",
        EARLY: "Early",
        PERCENTAGE: "Percentage",

        // Delay histogram
        DELAY_DISTRIBUTION: "Delay Distribution by Routes",
        ARRIVAL_COUNT: "Arrival Count",

        // Delay categories
        VERY_EARLY: "Very Early (< -2 min)",
        EARLY_CAT: "Early (-2 to -1 min)",
        SLIGHTLY_EARLY: "Slightly Early (-1 to 0 min)",
        ON_TIME_CAT: "On Time (±1 min)",
        SLIGHTLY_LATE: "Slightly Late (1-3 min)",
        LATE_CAT: "Late (3-5 min)",
        VERY_LATE: "Very Late (> 5 min)",

        // Route statistics table
        ROUTE_STATISTICS: "Route Statistics",
        ROUTE_COL: "Route",
        TOTAL_ARRIVALS: "Total Arrivals",
        AVG_DELAY: "Avg Delay",
        ON_TIME_PERCENT: "On Time",
        DELAY_DISTRIBUTION_COL: "Delay Distribution",

        // Time filters
        TIME_24H: "24h",
        TIME_48H: "48h",
        TIME_7D: "7 days",

        // Units and formatting
        MINUTES_ABBREV: "min",
        MINUTES_AVG: "min avg",
        MINUTES_UNIT: "min",
        METERS_AWAY: "away",
        ARRIVALS: "arrivals",

        // Station details modal
        STATION_DETAILS: "Station Details",
        ROUTE_STATISTICS_24H: "Route Statistics (24h)",
        RECENT_ARRIVALS: "Recent Arrivals",
        APPROACHING_BUSES: "Approaching Buses",
        DIRECTION: "Direction",
        MEASURED_AT: "Measured at",
        STATION_AWAY: "station away",
        STATIONS_AWAY: "stations away",
        ARRIVING_IN: "Arriving in",
        ARRIVING_NOW: "Arriving now",
        LATE_WORD: "late",
        EARLY_WORD: "early",
        AT_STOP: "at stop",
        AVG_DELAY_LABEL: "Avg delay:",
        EARLY_ARRIVAL: "Early:",

        // Error messages
        ERROR_SEARCH_STATIONS: "Failed to search stations",
        ERROR_GEOLOCATION_NOT_SUPPORTED: "Geolocation is not supported by this browser",
        ERROR_FIND_NEARBY: "Failed to find nearby stations",
        ERROR_GET_LOCATION: "Unable to get your location",
        ERROR_LOAD_STATION_DETAILS: "Failed to load station details",
        ERROR_LOAD_DATA: "Failed to load data",
        ERROR_LOAD_SYSTEM_STATS: "Unable to load system stats",
        ERROR_DATABASE: "Database error",
        ERROR_DATABASE_NOT_INITIALIZED: "Database not initialized. Please contact administrator.",
        ERROR_INVALID_COORDINATES: "Invalid coordinates",
        ERROR_STATION_NOT_FOUND: "Station not found",

        // Data states
        NO_DATA_AVAILABLE: "No data available",
        NO_STATIONS_FOUND: "No stations found",
        NO_NEARBY_STATIONS: "No nearby stations found",
        NO_DELAY_DATA: "No delay data available for this station.",
        NO_RECENT_DELAY_DATA: "No recent delay data available.",

        // Loading states
        SEARCHING: "Searching...",
        FINDING: "Finding...",

        // System stats labels
        TOTAL_RECORDS_STAT: "Total Records",
        ROUTES_STAT: "Routes",
        LAST_24H_STAT: "Last 24h",
        RECENT_DELAYS_STAT: "Recent Delays",
        LAST_UPDATE: "Last update:",

        // Codes and identifiers
        ID_LABEL: "ID:",
        CODE_LABEL: "Code:",

        // Common actions
        CLEAR: "Clear",
        SEARCH: "Search",
        VIEW: "View",

        // Speed legend labels
        SPEED_LEGEND_VERY_SLOW: "< 10",
        SPEED_LEGEND_SLOW: "10-20",
        SPEED_LEGEND_MODERATE: "20-40",
        SPEED_LEGEND_FAST: "40-60",
        SPEED_LEGEND_VERY_FAST: "> 60",

        // New bus tracking translations
        NO_BUSES_APPROACHING: "No buses approaching these stations",
        BUSES_WITH_NAME: "stations with this name",
        STATION_WITH_NAME: "station with this name",
        NO_BUSES_FOR_STATION: "No buses approaching",
        AT_STATION: "At station",
        LEAVING_STATION: "Leaving station",
        NEXT_STOP_IS_HERE: "Next stop is here",
        STOPS_AWAY_SINGLE: "stop away",
        STOPS_AWAY_PLURAL: "stops away",
        LOCATION_LABEL: "Location:",
        LAST_UPDATED_LABEL: "Last updated:",
        DELAY_INFO_TEMPLATE: "Arrived {time} {status} at last stop.",
        DELAY_STATUS_ON_TIME: "on time",
        DELAY_STATUS_LATE: "minutes late",
        DELAY_STATUS_EARLY: "minutes early"
    },

    IS: {
        // Application name and branding
        APP_NAME: "Strætó Vaktar",

        // Navigation
        NAV_STATION_SEARCH: "Stöðvaleit",
        NAV_ANALYTICS: "Greiningar",

        // Main page - Station search
        PAGE_TITLE_STATION_SEARCH: "Stöðvaleit - Strætó Vaktar",
        STATION_SEARCH_TITLE: "Finna Strætisvagnsstöð",
        MAIN_QUESTION: "Er strætó seinn?",
        SEARCH_BY_NAME: "Leit eftir nafni",
        SEARCH_PLACEHOLDER: "Sláðu inn nafn stöðvar...",
        FIND_NEARBY_STATIONS: "Finna nálægar stöðvar",
        USE_MY_LOCATION: "Nota staðsetningu mína",

        // How to use section
        HOW_TO_USE: "Hvernig á að nota",
        HOW_TO_SEARCH: "Leitaðu að stöðvum eftir nafni eða kóða",
        HOW_TO_LOCATION: "Finndu stöðvar nálægt þinni staðsetningu",
        HOW_TO_DELAYS: "Skoðaðu rauntíma töf upplýsingar",
        HOW_TO_ANALYTICS: "Athugaðu greiningar fyrir frammistöðu leiða",

        // System status
        SYSTEM_STATUS: "Kerfisstaða",
        LOADING: "Hleður...",
        CLOSE: "Loka",
        VIEW_ALL_DETAILS: "Skoða allar upplýsingar",

        // Analytics page
        PAGE_TITLE_ANALYTICS: "Greiningar - Strætó Vaktar",
        SYSTEM_ANALYTICS: "Kerfigreiningar",
        TOTAL_RECORDS: "Heildarskráningar",
        ACTIVE_ROUTES: "Virkar leiðir",
        LAST_24H: "Síðustu 24 klst",
        RECENT_DELAYS: "Nýlegar tafir",

        // Station-route analysis
        WORST_STATION_ROUTE_PAIRS: "Verstu stöðva-leið pör",
        MOST_DELAYED: "Mest töfin",
        MOST_EARLY: "Mesta fyrirtækni",

        // Speed heatmap
        SPEED_HEATMAP: "Hitakort hraða",
        SPEED_KMH: "Hraði (km/klst)",
        ROUTE: "Leið",
        SPEED: "Hraði",

        // Route performance
        ROUTE_PERFORMANCE: "Frammistöðu leiða",
        ON_TIME: "Á réttum tíma",
        LATE: "Seint",
        EARLY: "Snemma",
        PERCENTAGE: "Prósenta",

        // Delay histogram
        DELAY_DISTRIBUTION: "Töfadreifing eftir leiðum",
        ARRIVAL_COUNT: "Fjöldi komu",

        // Delay categories
        VERY_EARLY: "Mjög snemma (< -2 mín)",
        EARLY_CAT: "Snemma (-2 til -1 mín)",
        SLIGHTLY_EARLY: "Aðeins snemma (-1 til 0 mín)",
        ON_TIME_CAT: "Á réttum tíma (±1 mín)",
        SLIGHTLY_LATE: "Aðeins seint (1-3 mín)",
        LATE_CAT: "Seint (3-5 mín)",
        VERY_LATE: "Mjög seint (> 5 mín)",

        // Route statistics table
        ROUTE_STATISTICS: "Leiðartölfræði",
        ROUTE_COL: "Leið",
        TOTAL_ARRIVALS: "Heildar komur",
        AVG_DELAY: "Meðaltöf",
        ON_TIME_PERCENT: "Á réttum tíma",
        DELAY_DISTRIBUTION_COL: "Dreifing tafa",

        // Time filters
        TIME_24H: "24 klst",
        TIME_48H: "48 klst",
        TIME_7D: "7 dagar",

        // Units and formatting
        MINUTES_ABBREV: "mín",
        MINUTES_AVG: "mín meðal",
        MINUTES_UNIT: "mín",
        METERS_AWAY: "í burtu",
        ARRIVALS: "komur",

        // Station details modal
        STATION_DETAILS: "Stöðvarupplýsingar",
        ROUTE_STATISTICS_24H: "Leiðartölfræði (24 klst)",
        RECENT_ARRIVALS: "Nýlegar komur",
        APPROACHING_BUSES: "Vagnar á leið",
        DIRECTION: "Stefna",
        MEASURED_AT: "Mælt við",
        STATION_AWAY: "stöð í burtu",
        STATIONS_AWAY: "stöðvar í burtu",
        ARRIVING_IN: "Kemur eftir",
        ARRIVING_NOW: "Kemur núna",
        LATE_WORD: "seinn",
        EARLY_WORD: "snemma",
        AT_STOP: "á stoppið",
        AVG_DELAY_LABEL: "Meðaltöf:",
        EARLY_ARRIVAL: "Fyrirtækni:",

        // Error messages
        ERROR_SEARCH_STATIONS: "Gat ekki leitað að stöðvum",
        ERROR_GEOLOCATION_NOT_SUPPORTED: "Staðsetning er ekki studd í þessum vafra",
        ERROR_FIND_NEARBY: "Gat ekki fundið nálægar stöðvar",
        ERROR_GET_LOCATION: "Gat ekki náð í staðsetningu þína",
        ERROR_LOAD_STATION_DETAILS: "Gat ekki hlaðið upplýsingar um stöð",
        ERROR_LOAD_DATA: "Gat ekki hlaðið gögn",
        ERROR_LOAD_SYSTEM_STATS: "Gat ekki hlaðið kerfistölfræði",
        ERROR_DATABASE: "Villa í gagnagrunni",
        ERROR_DATABASE_NOT_INITIALIZED: "Gagnagrunnur ekki tilbúinn. Vinsamlegast hafðu samband við kerfisstjóra.",
        ERROR_INVALID_COORDINATES: "Ógild staðsetning",
        ERROR_STATION_NOT_FOUND: "Stöð fannst ekki",

        // Data states
        NO_DATA_AVAILABLE: "Engin gögn til staðar",
        NO_STATIONS_FOUND: "Engar stöðvar fundust",
        NO_NEARBY_STATIONS: "Engar nálægar stöðvar fundust",
        NO_DELAY_DATA: "Engin töfugögn til staðar fyrir þessa stöð.",
        NO_RECENT_DELAY_DATA: "Engin nýleg töfugögn til staðar.",

        // Loading states
        SEARCHING: "Leitar...",
        FINDING: "Finnur...",

        // System stats labels
        TOTAL_RECORDS_STAT: "Heildarskráningar",
        ROUTES_STAT: "Leiðir",
        LAST_24H_STAT: "Síðustu 24 klst",
        RECENT_DELAYS_STAT: "Nýlegar tafir",
        LAST_UPDATE: "Síðasta uppfærsla:",

        // Codes and identifiers
        ID_LABEL: "ID:",
        CODE_LABEL: "Kóði:",

        // Common actions
        CLEAR: "Hreinsa",
        SEARCH: "Leita",
        VIEW: "Skoða",

        // Speed legend labels
        SPEED_LEGEND_VERY_SLOW: "< 10",
        SPEED_LEGEND_SLOW: "10-20",
        SPEED_LEGEND_MODERATE: "20-40",
        SPEED_LEGEND_FAST: "40-60",
        SPEED_LEGEND_VERY_FAST: "> 60",

        // New bus tracking translations
        NO_BUSES_APPROACHING: "Engir strætó á leiðinni að þessum stöðvum",
        BUSES_WITH_NAME: "stöðvar með þessu nafni",
        STATION_WITH_NAME: "stöð með þessu nafni",
        NO_BUSES_FOR_STATION: "Engir strætó á leiðinni",
        AT_STATION: "Á þessu stoppi",
        LEAVING_STATION: "Á leið héðan",
        NEXT_STOP_IS_HERE: "Næsta stopp er hér",
        STOPS_AWAY_SINGLE: "stoppi frá",
        STOPS_AWAY_PLURAL: "stoppum frá",
        LOCATION_LABEL: "Staðsetning:",
        LAST_UPDATED_LABEL: "Síðast uppfært:",
        DELAY_INFO_TEMPLATE: "Kom {time} {status} á síðasta stopp.",
        DELAY_STATUS_ON_TIME: "á réttum tíma",
        DELAY_STATUS_LATE: "mínútum of seint",
        DELAY_STATUS_EARLY: "mínútum of snemma"
    }
};

// Current language (default to Icelandic)
let currentLanguage = 'IS';

// Helper function to get translation
function t(key) {
    return TRANSLATIONS[currentLanguage][key] || `[MISSING: ${currentLanguage}.${key}]`;
}

// Function to toggle language
function toggleLanguage() {
    currentLanguage = currentLanguage === 'EN' ? 'IS' : 'EN';

    // Save preference to localStorage
    localStorage.setItem('language', currentLanguage);

    // Apply translations immediately
    applyTranslations();

    // Update toggle button text
    updateLanguageToggleButton();

    // Dispatch custom event for other components to react
    document.dispatchEvent(new CustomEvent('languageChanged', {
        detail: { language: currentLanguage }
    }));
}

// Function to set language
function setLanguage(lang) {
    if (TRANSLATIONS[lang]) {
        currentLanguage = lang;
        localStorage.setItem('language', currentLanguage);
        applyTranslations();
        updateLanguageToggleButton();
        document.dispatchEvent(new CustomEvent('languageChanged', {
            detail: { language: currentLanguage }
        }));
    }
}

// Function to get current language
function getCurrentLanguage() {
    return currentLanguage;
}

// Apply translations to elements with data-translate attributes
function applyTranslations() {
    document.querySelectorAll('[data-translate]').forEach(element => {
        const key = element.getAttribute('data-translate');
        const translation = t(key);
        element.textContent = translation;
    });

    // Handle placeholder translations
    document.querySelectorAll('[data-translate-placeholder]').forEach(element => {
        const key = element.getAttribute('data-translate-placeholder');
        const translation = t(key);
        element.placeholder = translation;
    });

    // Handle title translations
    document.querySelectorAll('[data-translate-title]').forEach(element => {
        const key = element.getAttribute('data-translate-title');
        const translation = t(key);
        element.title = translation;
    });

    // Update page title
    const titleElement = document.querySelector('title');
    if (titleElement) {
        const pageName = document.body.dataset.page || '';
        let titleKey = '';

        switch(pageName) {
            case 'analytics':
                titleKey = 'PAGE_TITLE_ANALYTICS';
                break;
            case 'station-search':
            default:
                titleKey = 'PAGE_TITLE_STATION_SEARCH';
                break;
        }

        if (titleKey && TRANSLATIONS[currentLanguage][titleKey]) {
            titleElement.textContent = t(titleKey);
        }
    }
}

// Update language toggle button text
function updateLanguageToggleButton() {
    const toggleButton = document.getElementById('languageToggle');
    if (toggleButton) {
        toggleButton.textContent = currentLanguage === 'EN' ? 'IS' : 'EN';
        toggleButton.title = currentLanguage === 'EN' ? 'Switch to Icelandic' : 'Switch to English';
    }
}

// Initialize language from localStorage or default to Icelandic
function initializeLanguage() {
    const savedLanguage = localStorage.getItem('language');
    if (savedLanguage && TRANSLATIONS[savedLanguage]) {
        currentLanguage = savedLanguage;
    }
    applyTranslations();
    updateLanguageToggleButton();
}

// Auto-apply translations when DOM is loaded
document.addEventListener('DOMContentLoaded', initializeLanguage);

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { TRANSLATIONS, t, applyTranslations, toggleLanguage, setLanguage, getCurrentLanguage };
}