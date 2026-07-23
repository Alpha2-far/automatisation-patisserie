from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from pathlib import Path

from app.services.processor import batch_process_pending_uploads, get_processing_status
from app.db import (
    get_processed_products,
    get_processed_product_by_id,
    delete_processed_product,
    clear_all_processed_products
)
from app.config import BASE_DIR

router = APIRouter(prefix="/api/process", tags=["process"])

class ProcessRequest(BaseModel):
    category_slug: Optional[str] = None
    mode: Optional[str] = "crop"

@router.post("", status_code=status.HTTP_200_OK)
def trigger_processing(payload: Optional[ProcessRequest] = None):
    """Trigger product photo cropping or background removal for pending uploads."""
    category_slug = payload.category_slug if payload else None
    mode = payload.mode if (payload and payload.mode) else "crop"
    try:
        results = batch_process_pending_uploads(category_slug=category_slug, mode=mode)
        return {
            "success": True,
            "results": results
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors du traitement d'image : {str(e)}"
        )

@router.get("/status")
def get_status():
    """Get real-time batch processing progress status."""
    return get_processing_status()

@router.get("/products", response_model=List[Dict[str, Any]])
def list_processed_products(category_slug: Optional[str] = None):
    """Retrieve processed products list."""
    return get_processed_products(category_slug=category_slug)

@router.delete("/products/clear", status_code=status.HTTP_200_OK)
def clear_gallery(category_slug: Optional[str] = None):
    """Clear all processed products for a category or globally."""
    products = get_processed_products(category_slug=category_slug)
    for p in products:
        file_path = BASE_DIR / p["file_path"]
        if file_path.exists():
            try:
                file_path.unlink()
            except Exception:
                pass
    clear_all_processed_products(category_slug=category_slug)
    return {"success": True, "message": f"{len(products)} produit(s) effacé(s) de la galerie."}

@router.delete("/products/{product_id}", status_code=status.HTTP_200_OK)
def remove_processed_product(product_id: int):
    """Delete a processed product from database and disk."""
    product = get_processed_product_by_id(product_id)
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Produit #{product_id} introuvable."
        )

    file_path = BASE_DIR / product["file_path"]
    if file_path.exists():
        try:
            file_path.unlink()
        except Exception:
            pass

    delete_processed_product(product_id)
    return {"success": True, "message": f"Produit #{product_id} supprimé."}
