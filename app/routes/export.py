from fastapi import APIRouter, HTTPException, status
from fastapi.responses import FileResponse
from typing import Optional

from app.services.exporter import (
    create_category_zip,
    create_all_categories_zip,
    get_excel_registry_path
)

router = APIRouter(prefix="/api/export", tags=["export"])

@router.get("/zip/{category_slug}")
def download_category_zip(category_slug: str):
    """Download ZIP archive of clean images for a specific category."""
    try:
        zip_path = create_category_zip(category_slug)
        if not zip_path.exists():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Aucune image trouvée pour la catégorie '{category_slug}'."
            )
        return FileResponse(
            path=zip_path,
            filename=f"{category_slug}_catalogue.zip",
            media_type="application/zip"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de la création du fichier ZIP : {str(e)}"
        )

@router.get("/zip")
def download_all_zip():
    """Download master ZIP archive of all category folders and clean images."""
    try:
        zip_path = create_all_categories_zip()
        return FileResponse(
            path=zip_path,
            filename="catalogue_global_images.zip",
            media_type="application/zip"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de la création du ZIP global : {str(e)}"
        )

@router.get("/excel")
def download_excel_registry():
    """Download central Excel registry (catalogue_global.xlsx)."""
    try:
        excel_path = get_excel_registry_path()
        if not excel_path.exists():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Le fichier Excel récapitulatif n'a pas encore été généré."
            )
        return FileResponse(
            path=excel_path,
            filename="catalogue_global.xlsx",
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors du téléchargement d'Excel : {str(e)}"
        )
