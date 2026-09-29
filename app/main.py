from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pathlib import Path

from app.config import BASE_DIR, UPLOADS_BRUTS_DIR, CATALOGUE_FINAL_DIR, ensure_directories_exist
from app.db import init_db, get_db
from app.services.excel import ensure_excel_registry_exists
from app.routes import categories, upload, process, export

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Modern lifespan context manager for startup and shutdown events."""
    ensure_directories_exist()
    init_db()
    ensure_excel_registry_exists()
    yield

app = FastAPI(
    title="Pâtisserie Catalogue Automatique",
    description="Interface d'importation et d'automatisation de catalogue pâtisserie",
    version="1.1.0",
    lifespan=lifespan
)

# Mount Static, Uploads & Final Catalogue Directories
static_dir = BASE_DIR / "app" / "static"
static_dir.mkdir(parents=True, exist_ok=True)

app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")
app.mount("/uploads_bruts", StaticFiles(directory=str(UPLOADS_BRUTS_DIR)), name="uploads_bruts")
app.mount("/catalogue_final", StaticFiles(directory=str(CATALOGUE_FINAL_DIR)), name="catalogue_final")

# Set up Templates
templates_dir = BASE_DIR / "app" / "templates"
templates_dir.mkdir(parents=True, exist_ok=True)
templates = Jinja2Templates(directory=str(templates_dir))

# Include API Routers
app.include_router(categories.router)
app.include_router(upload.router)
app.include_router(process.router)
app.include_router(export.router)

@app.get("/api/health", tags=["system"])
def health_check():
    """Health check endpoint verifying database connectivity and storage readiness."""
    db_ok = False
    try:
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT 1;")
            db_ok = cursor.fetchone()[0] == 1
    except Exception:
        db_ok = False

    return {
        "status": "healthy" if db_ok else "unhealthy",
        "database": "connected" if db_ok else "error",
        "uploads_dir": UPLOADS_BRUTS_DIR.exists(),
        "catalogue_dir": CATALOGUE_FINAL_DIR.exists(),
        "version": app.version
    }

@app.get("/")
def render_index(request: Request):
    """Render main application dashboard."""
    return templates.TemplateResponse(request=request, name="index.html")

