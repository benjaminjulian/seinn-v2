# Centralized translations for Strætó Vaktar Flask backend
# All user-facing text is collected here for easy translation and proofreading

TRANSLATIONS = {
    # Error messages for API responses
    "ERROR_DATABASE": "Villa í gagnagrunni",
    "ERROR_DATABASE_NOT_INITIALIZED": "Gagnagrunnur ekki tilbúinn. Vinsamlegast hafðu samband við kerfisstjóra.",
    "ERROR_INVALID_COORDINATES": "Ógild staðsetning",
    "ERROR_STATION_NOT_FOUND": "Stöð fannst ekki",

    # Success messages
    "SUCCESS_DATABASE_INITIALIZED": "Gagnagrunnur tilbúinn með GTFS gögnum",
    "SUCCESS_DATABASE_INITIALIZED_NO_GTFS": "Gagnagrunnur tilbúinn en GTFS niðurhal mistókst",
    "SUCCESS_MONITOR_TEST": "✅ Prófun á vöktun tókst",
    "SUCCESS_MONITOR_STARTED": "✅ Bakgrunnsvöktun ræst",
    "SUCCESS_MONITOR_STOPPED": "✅ Bakgrunnsvöktun stöðvuð",

    # Failure messages
    "FAILED_DATABASE_INITIALIZATION": "Gagnagrunnur gat ekki verið tilbúinn",
    "FAILED_MONITOR_TEST": "❌ Prófun á vöktun mistókst",
    "FAILED_MONITOR_START": "❌ Gat ekki ræst vöktun",
    "FAILED_MONITOR_STOP": "❌ Gat ekki stöðvað vöktun",

    # Configuration errors
    "ERROR_DATABASE_URL_NOT_SET": "DATABASE_URL ekki stillt",
    "ERROR_DATABASE_CONNECTION_FAILED": "Tenging við gagnagrunn mistókst",

    # Health check responses
    "HEALTH_OK": "OK",
    "HEALTH_DATABASE_FAILED": "Tenging við gagnagrunn mistókst",

    # Data states
    "NO_DATA_AVAILABLE": "Engin gögn til staðar",
    "TABLE_NOT_EXISTS": "❌ Tafla er ekki til",
    "TABLE_ERROR": "⚠️ Villa:",
    "TABLE_RECORDS": "✅ skrár",
    "ACTIVE_GTFS_VERSIONS": "✅ virk GTFS útgáfa(r)",
    "NO_ACTIVE_GTFS": "❌ Engin virk GTFS útgáfa",
    "CANNOT_CHECK_GTFS": "❌ Gat ekki athugað GTFS útgáfur",

    # Migration and database operations
    "MIGRATION_SUCCESS": "✅ Gagnagrunnsfærsla tókst",
    "MIGRATION_FAILED": "❌ Gagnagrunnsfærsla mistókst",

    # Monitor status
    "MONITOR_RUNNING_YES": "✅ Já",
    "MONITOR_RUNNING_NO": "❌ Nei",
    "DATABASE_CONFIGURED_YES": "✅ Stillt",
    "DATABASE_CONFIGURED_NO": "❌ Ekki stillt",
}

def t(key, default=None):
    """Get translation for a key, with optional default value."""
    if default is None:
        default = f"[MISSING: {key}]"
    return TRANSLATIONS.get(key, default)