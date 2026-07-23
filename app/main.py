from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pathlib import Path

from app.config import BASE_DIR, UPLOADS_BRUTS_DIR, CATALOGUE_FINAL_DIR, ensure_directories_exist
from app.db import init_db
from app.routes import categories, upload, process, export

# Initialize Directories and DB Schema
ensure_directories_exist()
init_db()

app = FastAPI(
    title="Pâtisserie Catalogue Automatique",
    description="Interface d'importation et d'automatisation de catalogue pâtisserie",
    version="1.0.0"
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

@app.get("/")
def render_index(request: Request):
    """Render main application dashboard."""
    return templates.TemplateResponse(request=request, name="index.html")
