import shutil
import uuid
from pathlib import Path
from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, status
from app.config import BASE_DIR, UPLOADS_BRUTS_DIR, ALLOWED_EXTENSIONS, MAX_FILE_SIZE_BYTES
from app.db import (
    get_category_by_slug,
    create_raw_upload,
    get_raw_uploads,
    get_raw_upload_by_id,
    delete_raw_upload,
    clear_all_raw_uploads,
    slugify
)

router = APIRouter(prefix="/api/uploads", tags=["uploads"])

@router.post("", status_code=status.HTTP_201_CREATED)
async def upload_files(
    category_slug: str = Form(...),
    files: List[UploadFile] = File(...)
):
    """Multi-file upload handler for raw screenshots."""
    category = get_category_by_slug(category_slug)
    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Catégorie '{category_slug}' introuvable."
        )

    cat_dir = UPLOADS_BRUTS_DIR / category_slug
    cat_dir.mkdir(parents=True, exist_ok=True)

    saved_uploads = []
    errors = []

    for file in files:
        file_ext = Path(file.filename).suffix.lower()
        if file_ext not in ALLOWED_EXTENSIONS:
            errors.append(f"Format non supporté pour '{file.filename}'. Formats autorisés: PNG, JPG, JPEG, WEBP.")
            continue

        # Generate safe unique filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        unique_id = uuid.uuid4().hex[:6]
        base_name = slugify(Path(file.filename).stem) or "capture"
        unique_filename = f"{timestamp}_{unique_id}_{base_name}{file_ext}"

        file_path = cat_dir / unique_filename

        try:
            # Read content & check size
            contents = await file.read()
            file_size = len(contents)

            if file_size > MAX_FILE_SIZE_BYTES:
                errors.append(f"Le fichier '{file.filename}' dépasse la limite de 20 Mo.")
                continue

            with open(file_path, "wb") as f:
                f.write(contents)

            # Record in database
            rel_path = f"uploads_bruts/{category_slug}/{unique_filename}"
            upload_record = create_raw_upload(
                filename=unique_filename,
                original_filename=file.filename,
                category_slug=category_slug,
                file_path=rel_path,
                file_size=file_size
            )
            saved_uploads.append(upload_record)

        except Exception as e:
            errors.append(f"Erreur lors de l'enregistrement de '{file.filename}': {str(e)}")

    return {
        "success": len(saved_uploads) > 0,
        "uploaded_count": len(saved_uploads),
        "uploads": saved_uploads,
        "errors": errors
    }

@router.get("")
def list_uploads(category_slug: Optional[str] = None):
    """Retrieve raw uploads list, optionally filtered by category."""
    return get_raw_uploads(category_slug=category_slug)

@router.delete("/clear", status_code=status.HTTP_200_OK)
def clear_raw_uploads_gallery(category_slug: Optional[str] = None):
    """Delete all raw upload files for a category or globally."""
    uploads = get_raw_uploads(category_slug=category_slug)
    for u in uploads:
        file_path = BASE_DIR / u["file_path"]
        if file_path.exists():
            try:
                file_path.unlink()
            except Exception:
                pass
    clear_all_raw_uploads(category_slug=category_slug)
    return {"success": True, "message": f"{len(uploads)} capture(s) effacée(s)."}

@router.delete("/{upload_id}")
def delete_upload(upload_id: int):
    """Delete a raw upload file from disk and database."""
    record = get_raw_upload_by_id(upload_id)
    if not record:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Fichier non trouvé.")

    # Remove file from disk if it exists
    file_path = BASE_DIR / record["file_path"]
    if file_path.exists():
        try:
            file_path.unlink()
        except Exception as e:
            print(f"Warning: Could not remove file {file_path}: {e}")

    delete_raw_upload(upload_id)
    return {"success": True, "message": "Fichier supprimé avec succès."}
