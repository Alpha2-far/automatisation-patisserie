from pathlib import Path

# Project Base Directory
BASE_DIR = Path(__file__).resolve().parent.parent

# Storage Directories
UPLOADS_BRUTS_DIR = BASE_DIR / "uploads_bruts"
CATALOGUE_FINAL_DIR = BASE_DIR / "catalogue_final"

# Database Location
DB_PATH = BASE_DIR / "database.db"

# Allowed Upload Settings
ALLOWED_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp"}
MAX_FILE_SIZE_BYTES = 20 * 1024 * 1024  # 20 MB

def ensure_directories_exist():
    """Ensure that storage directories exist on disk."""
    UPLOADS_BRUTS_DIR.mkdir(parents=True, exist_ok=True)
    CATALOGUE_FINAL_DIR.mkdir(parents=True, exist_ok=True)
