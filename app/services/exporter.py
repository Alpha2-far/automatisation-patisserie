import zipfile
from pathlib import Path
from typing import Optional
from app.config import CATALOGUE_FINAL_DIR

def create_category_zip(category_slug: str) -> Path:
    """
    Creates a ZIP archive containing all clean product PNGs for a given category.
    Returns path to the created ZIP file.
    """
    category_dir = CATALOGUE_FINAL_DIR / category_slug
    if not category_dir.exists():
        category_dir.mkdir(parents=True, exist_ok=True)

    zip_filename = f"{category_slug}_catalogue.zip"
    zip_path = CATALOGUE_FINAL_DIR / zip_filename

    image_files = list(category_dir.glob("*.png")) + list(category_dir.glob("*.jpg")) + list(category_dir.glob("*.jpeg"))

    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zipf:
        for img in image_files:
            zipf.write(img, arcname=img.name)

    return zip_path

def create_all_categories_zip() -> Path:
    """
    Creates a ZIP archive containing all category folders and clean images.
    Returns path to the master ZIP file.
    """
    zip_filename = "catalogue_global_images.zip"
    zip_path = CATALOGUE_FINAL_DIR / zip_filename

    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zipf:
        for item in CATALOGUE_FINAL_DIR.rglob("*"):
            if item.is_file() and not item.name.endswith(".zip") and not item.name.startswith("."):
                rel_path = item.relative_to(CATALOGUE_FINAL_DIR)
                zipf.write(item, arcname=str(rel_path))

    return zip_path

def get_excel_registry_path() -> Path:
    """Returns path to central Excel registry file."""
    excel_path = CATALOGUE_FINAL_DIR / "catalogue_global.xlsx"
    if not excel_path.exists():
        from app.services.excel import ensure_excel_registry_exists
        ensure_excel_registry_exists()
    return excel_path
