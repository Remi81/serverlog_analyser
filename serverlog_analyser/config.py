"""Configuration centralisée pour serverlog_analyser.

Valeurs lisibles via variables d'environnement pour faciliter le déploiement.
"""
import os


def _get_bool(name: str, default: bool) -> bool:
    v = os.getenv(name)
    if v is None:
        return default
    return v.lower() in ("1", "true", "yes", "on")

# --- Behaviour flags
DELETE_UPLOADS_AFTER_PROCESSING: bool = _get_bool("DELETE_UPLOADS_AFTER_PROCESSING", True)
SHOW_VARIANTS_BY_DEFAULT: bool = _get_bool("SHOW_VARIANTS_BY_DEFAULT", False)

# --- Display limits (can be tuned via env)
TOP_N_IPS: int = int(os.getenv("TOP_N_IPS", "20"))
TOP_N_PATHS: int = int(os.getenv("TOP_N_PATHS", "20"))
AGGREGATED_LIMIT: int = int(os.getenv("AGGREGATED_LIMIT", "500"))

# --- Other useful defaults
MAX_URL_TREE_DEPTH: int = int(os.getenv("MAX_URL_TREE_DEPTH", "10"))

# Helper: export a small dict usable by the frontend
def as_frontend_dict():
    return {
        "delete_uploads_after_processing": DELETE_UPLOADS_AFTER_PROCESSING,
        "show_variants_by_default": SHOW_VARIANTS_BY_DEFAULT,
        "top_n_ips": TOP_N_IPS,
        "top_n_paths": TOP_N_PATHS,
        "aggregated_limit": AGGREGATED_LIMIT,
        "max_url_tree_depth": MAX_URL_TREE_DEPTH,
    }
