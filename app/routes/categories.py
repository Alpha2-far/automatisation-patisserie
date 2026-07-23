from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from app.db import get_all_categories, create_category, get_category_by_slug, delete_category_by_slug

router = APIRouter(prefix="/api/categories", tags=["categories"])

class CategoryCreateRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=100, description="Nom de la catégorie")
    price: Optional[str] = Field(None, description="Prix optionnel (ex: 15 000 FCFA)")

@router.get("", response_model=List[Dict[str, Any]])
def list_categories():
    """Retrieve all product categories with stats."""
    return get_all_categories()

@router.post("", status_code=status.HTTP_201_CREATED)
def add_category(payload: CategoryCreateRequest):
    """Create a new category dynamically."""
    try:
        category = create_category(payload.name, price=payload.price)
        return {"success": True, "category": category}
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Erreur serveur: {str(e)}")

@router.delete("/{slug}")
def remove_category(slug: str):
    """Delete a category by slug."""
    category = get_category_by_slug(slug)
    if not category:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Catégorie non trouvée.")
    
    delete_category_by_slug(slug)
    return {"success": True, "message": f"Catégorie '{category['name']}' supprimée."}
