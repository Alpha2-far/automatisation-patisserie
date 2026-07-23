import io
import re
from pathlib import Path
from typing import Optional, List, Dict, Any
from PIL import Image, ImageOps, ImageFile
import cv2
import numpy as np
import rembg

# Allow Pillow to load truncated/imperfect JPEG uploads from mobile devices
ImageFile.LOAD_TRUNCATED_IMAGES = True

from app.config import BASE_DIR, UPLOADS_BRUTS_DIR, CATALOGUE_FINAL_DIR
from app.db import (
    get_raw_uploads,
    get_pending_raw_uploads,
    update_raw_upload_status,
    create_processed_product,
    get_category_by_slug,
    slugify,
    parse_price
)
from app.services.excel import append_to_excel_registry

# Shared rembg session instance to avoid reloading ONNX model repeatedly
_rembg_session = None

def get_rembg_session():
    global _rembg_session
    if _rembg_session is None:
        _rembg_session = rembg.new_session("u2net")
    return _rembg_session

# Global processing status state
_processing_status: Dict[str, Any] = {
    "is_processing": False,
    "current_step": 0,
    "total_steps": 0,
    "current_filename": "",
    "mode": "crop"
}

def get_processing_status() -> Dict[str, Any]:
    """Returns current real-time processing progress status."""
    return _processing_status

def detect_product_photo_box(img_path: Path) -> tuple:
    """
    Detects the primary product photo container in a screenshot using gradient texture analysis.
    Returns (left, upper, right, lower) cropping coordinates.
    """
    try:
        img_cv = cv2.imread(str(img_path))
        if img_cv is None:
            with Image.open(img_path) as pimg:
                return (0, 0, pimg.width, pimg.height)

        h, w, _ = img_cv.shape
        
        gray = cv2.cvtColor(img_cv, cv2.COLOR_BGR2GRAY)
        grad_x = cv2.Sobel(gray, cv2.CV_32F, 1, 0, ksize=3)
        grad_y = cv2.Sobel(gray, cv2.CV_32F, 0, 1, ksize=3)
        magnitude = cv2.magnitude(grad_x, grad_y)
        
        mag_norm = cv2.normalize(magnitude, None, 0, 255, cv2.NORM_MINMAX).astype(np.uint8)
        
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (15, 15))
        closed = cv2.morphologyEx(mag_norm, cv2.MORPH_CLOSE, kernel)
        _, thresh = cv2.threshold(closed, 20, 255, cv2.THRESH_BINARY)
        
        contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        candidates = []
        for cnt in contours:
            x, y, cw, ch = cv2.boundingRect(cnt)
            area = cw * ch
            if (0.10 * w * h) < area < (0.95 * w * h):
                aspect = cw / float(ch)
                if 0.4 <= aspect <= 2.5:
                    candidates.append((x, y, cw, ch, area))
                
        if candidates:
            candidates.sort(key=lambda c: c[4], reverse=True)
            x, y, cw, ch, _ = candidates[0]
            
            margin = 10
            x1 = max(0, x - margin)
            y1 = max(0, y - margin)
            x2 = min(w, x + cw + margin)
            y2 = min(h, y + ch + margin)
            return (x1, y1, x2, y2)
            
        return (0, 0, w, h)
    except Exception:
        with Image.open(img_path) as pimg:
            return (0, 0, pimg.width, pimg.height)

def auto_crop_alpha(img: Image.Image, padding: int = 15) -> Image.Image:
    """Crops transparent RGBA image to alpha bounding box."""
    if img.mode != 'RGBA':
        img = img.convert('RGBA')

    alpha = img.split()[-1]
    bbox = alpha.getbbox()

    if not bbox:
        return img

    left, upper, right, lower = bbox
    w, h = img.size
    left = max(0, left - padding)
    upper = max(0, upper - padding)
    right = min(w, right + padding)
    lower = min(h, lower + padding)

    return img.crop((left, upper, right, lower))

def process_single_upload(upload_record: Dict[str, Any], mode: str = "crop") -> Dict[str, Any]:
    """Process a single raw upload record."""
    upload_id = upload_record["id"]
    category_slug = upload_record["category_slug"]
    original_filename = upload_record["original_filename"]
    raw_file_rel_path = upload_record["file_path"]

    raw_file_abs_path = BASE_DIR / raw_file_rel_path
    if not raw_file_abs_path.exists():
        update_raw_upload_status(upload_id, "erreur")
        raise FileNotFoundError(f"Fichier brut introuvable : {raw_file_abs_path}")

    update_raw_upload_status(upload_id, "en_cours")

    cat_final_dir = CATALOGUE_FINAL_DIR / category_slug
    cat_final_dir.mkdir(parents=True, exist_ok=True)

    stem_name = Path(original_filename).stem
    clean_stem = slugify(stem_name) or "produit"
    output_filename = f"{clean_stem}_{upload_id}.png"
    output_file_abs_path = cat_final_dir / output_filename
    rel_output_path = f"catalogue_final/{category_slug}/{output_filename}"

    try:
        with Image.open(raw_file_abs_path) as input_img:
            # Fix EXIF orientation (mobile cameras)
            input_img = ImageOps.exif_transpose(input_img)

            if mode == "rembg":
                session = get_rembg_session()
                rembg_out = rembg.remove(input_img, session=session)
                processed_img = auto_crop_alpha(rembg_out, padding=15)
            else:
                box = detect_product_photo_box(raw_file_abs_path)
                processed_img = input_img.crop(box)

            processed_img.save(output_file_abs_path, format="PNG")

        category_data = get_category_by_slug(category_slug)
        category_name = category_data["name"] if category_data else category_slug
        
        category_price = category_data.get("price", "") if category_data else ""
        _, file_price = parse_price(original_filename)
        final_price = category_price or file_price or ""

        excel_path = append_to_excel_registry(
            category_name=category_name,
            product_filename=output_filename,
            file_path=rel_output_path,
            price=final_price
        )

        processed_record = create_processed_product(
            category_slug=category_slug,
            raw_upload_id=upload_id,
            product_name=output_filename,
            file_path=rel_output_path,
            price=final_price
        )

        update_raw_upload_status(upload_id, "succes")

        return {
            "success": True,
            "raw_upload_id": upload_id,
            "processed_product": processed_record,
            "excel_path": excel_path
        }

    except Exception as e:
        update_raw_upload_status(upload_id, "erreur")
        raise e

def batch_process_pending_uploads(category_slug: Optional[str] = None, mode: str = "crop") -> Dict[str, Any]:
    """Batch process all pending (or all if pending empty) raw uploads with real-time status tracking."""
    global _processing_status
    pending = get_pending_raw_uploads(category_slug=category_slug)
    
    # If no pending uploads, process all raw uploads in category as fallback
    if len(pending) == 0:
        pending = get_raw_uploads(category_slug=category_slug)

    total_steps = len(pending)

    _processing_status = {
        "is_processing": True,
        "current_step": 0,
        "total_steps": total_steps,
        "current_filename": "",
        "mode": mode
    }

    successful = []
    failed = []

    try:
        for idx, record in enumerate(pending, start=1):
            _processing_status["current_step"] = idx
            _processing_status["current_filename"] = record["original_filename"]

            try:
                res = process_single_upload(record, mode=mode)
                successful.append(res)
            except Exception as e:
                failed.append({
                    "raw_upload_id": record["id"],
                    "original_filename": record["original_filename"],
                    "error": str(e)
                })

    finally:
        _processing_status["is_processing"] = False
        _processing_status["current_filename"] = ""

    return {
        "total_pending": total_steps,
        "processed_count": len(successful),
        "failed_count": len(failed),
        "successful": successful,
        "failed": failed
    }
