// Centralized translations for Strætó Vaktar
// All user-facing text is collected here for easy translation and proofreading

const TRANSLATIONS = {
    // Application name and branding
    APP_NAME: "Strætó Vaktar",

    // Navigation
    NAV_STATION_SEARCH: "Stöðvaleit",
    NAV_ANALYTICS: "Greiningar",

    // Main page - Station search
    PAGE_TITLE_STATION_SEARCH: "Stöðvaleit - Strætó Vaktar",
    STATION_SEARCH_TITLE: "Finna Strætisvagnsstöð",
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
    SPEED_LEGEND_VERY_FAST: "> 60"
};

// Helper function to get translation
function t(key) {
    return TRANSLATIONS[key] || `[MISSING: ${key}]`;
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
}

// Auto-apply translations when DOM is loaded
document.addEventListener('DOMContentLoaded', applyTranslations);

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { TRANSLATIONS, t, applyTranslations };
}