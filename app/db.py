import sqlite3
import re
import unicodedata
from datetime import datetime
from typing import List, Dict, Any, Optional
from app.config import DB_PATH, UPLOADS_BRUTS_DIR

def slugify(text: str) -> str:
    """Convert text to URL-safe slug stripping accents and special characters."""
    text = unicodedata.normalize('NFKD', text).encode('ascii', 'ignore').decode('utf-8')
    text = text.lower().strip()
    text = re.sub(r'[^\w\s-]', '', text)
    text = re.sub(r'[\s_-]+', '_', text)
    return text.strip('_')

def parse_price(text: str) -> tuple:
    """
    Extracts price from string (e.g. 'Gâteau d'anniversaire à 15000 francs').
    Returns (cleaned_name, formatted_price).
    """
    price_regex = r'(?:à\s*)?(\d{1,3}(?:[\s\.]?\d{3})*|\d+)\s*(?:francs?|fcfa|f\b)'
    match = re.search(price_regex, text, re.IGNORECASE)
    
    if not match:
        fallback_regex = r'(\d{1,3}(?:[\s\.]?\d{3})*|\d+)\s*(?:f\b|francs?|fcfa)'
        match = re.search(fallback_regex, text, re.IGNORECASE)

    if match:
        raw_num = match.group(1).replace(" ", "").replace(".", "")
        try:
            num = int(raw_num)
            formatted_price = f"{num:,}".replace(",", " ") + " FCFA"
            clean_name = re.sub(r'\s*(?:à\s*)?' + re.escape(match.group(0)) + r'\s*', ' ', text, flags=re.IGNORECASE).strip()
            return (clean_name or text), formatted_price
        except ValueError:
            pass

    return text.strip(), ""

def get_db():
    """Return a database connection with dict-like row factory."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Initialize database schema with price columns."""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS categories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                slug TEXT NOT NULL UNIQUE,
                price TEXT DEFAULT '',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        
        cursor.execute("PRAGMA table_info(categories);")
        columns = [column[1] for column in cursor.fetchall()]
        if "price" not in columns:
            cursor.execute("ALTER TABLE categories ADD COLUMN price TEXT DEFAULT '';")

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS raw_uploads (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                filename TEXT NOT NULL,
                original_filename TEXT NOT NULL,
                category_slug TEXT NOT NULL,
                file_path TEXT NOT NULL,
                file_size INTEGER NOT NULL,
                status TEXT DEFAULT 'en_attente',
                uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (category_slug) REFERENCES categories (slug) ON DELETE CASCADE
            );
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS processed_products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                category_slug TEXT NOT NULL,
                raw_upload_id INTEGER,
                product_name TEXT NOT NULL,
                price TEXT DEFAULT '',
                file_path TEXT NOT NULL,
                processed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (category_slug) REFERENCES categories (slug) ON DELETE CASCADE,
                FOREIGN KEY (raw_upload_id) REFERENCES raw_uploads (id) ON DELETE SET NULL
            );
        """)

        cursor.execute("PRAGMA table_info(processed_products);")
        p_columns = [column[1] for column in cursor.fetchall()]
        if "price" not in p_columns:
            cursor.execute("ALTER TABLE processed_products ADD COLUMN price TEXT DEFAULT '';")

        conn.commit()

# --- Category Functions ---

def get_all_categories() -> List[Dict[str, Any]]:
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT c.id, c.name, c.slug, c.price, c.created_at,
                   COUNT(r.id) as upload_count,
                   (SELECT COUNT(*) FROM processed_products p WHERE p.category_slug = c.slug) as processed_count
            FROM categories c
            LEFT JOIN raw_uploads r ON c.slug = r.category_slug
            GROUP BY c.id
            ORDER BY c.name ASC;
        """)
        return [dict(row) for row in cursor.fetchall()]

def get_category_by_slug(slug: str) -> Optional[Dict[str, Any]]:
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM categories WHERE slug = ?;", (slug,))
        row = cursor.fetchone()
        return dict(row) if row else None

def create_category(name: str, price: Optional[str] = None) -> Dict[str, Any]:
    clean_name, extracted_price = parse_price(name)
    final_name = clean_name if clean_name else name
    final_price = price.strip() if price else extracted_price

    # Include price amount in slug to differentiate same-name categories with different prices
    # e.g. "Gâteau d'anniversaire 10000F" and "... 20000F" → gateau_danniversaire_10000 vs _20000
    slug = slugify(final_name)
    if final_price:
        # Extract raw digits from formatted price like "15 000 FCFA" → "15000"
        price_digits = re.sub(r'[^\d]', '', final_price)
        if price_digits:
            slug = f"{slug}_{price_digits}"

    if not slug:
        raise ValueError("Le nom de la catégorie n'est pas valide.")
    
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM categories WHERE slug = ?;", (slug,))
        if cursor.fetchone():
            raise ValueError(f"Une catégorie avec le slug '{slug}' existe déjà.")
        
        cursor.execute(
            "INSERT INTO categories (name, slug, price) VALUES (?, ?, ?);",
            (final_name, slug, final_price)
        )
        conn.commit()
        cat_id = cursor.lastrowid
        
        (UPLOADS_BRUTS_DIR / slug).mkdir(parents=True, exist_ok=True)
        
        return {
            "id": cat_id,
            "name": final_name,
            "slug": slug,
            "price": final_price,
            "created_at": datetime.now().isoformat()
        }

def delete_category_by_slug(slug: str):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM categories WHERE slug = ?;", (slug,))
        conn.commit()

# --- Raw Upload Functions ---

def create_raw_upload(filename: str, original_filename: str, category_slug: str, file_path: str, file_size: int) -> Dict[str, Any]:
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO raw_uploads (filename, original_filename, category_slug, file_path, file_size)
            VALUES (?, ?, ?, ?, ?);
        """, (filename, original_filename, category_slug, file_path, file_size))
        conn.commit()
        upload_id = cursor.lastrowid
        
        cursor.execute("SELECT * FROM raw_uploads WHERE id = ?;", (upload_id,))
        return dict(cursor.fetchone())

def get_raw_uploads(category_slug: Optional[str] = None) -> List[Dict[str, Any]]:
    with get_db() as conn:
        cursor = conn.cursor()
        if category_slug:
            cursor.execute("""
                SELECT r.*, c.name as category_name
                FROM raw_uploads r
                JOIN categories c ON r.category_slug = c.slug
                WHERE r.category_slug = ?
                ORDER BY r.uploaded_at DESC;
            """, (category_slug,))
        else:
            cursor.execute("""
                SELECT r.*, c.name as category_name
                FROM raw_uploads r
                JOIN categories c ON r.category_slug = c.slug
                ORDER BY r.uploaded_at DESC;
            """)
        return [dict(row) for row in cursor.fetchall()]

def get_pending_raw_uploads(category_slug: Optional[str] = None) -> List[Dict[str, Any]]:
    with get_db() as conn:
        cursor = conn.cursor()
        if category_slug:
            cursor.execute("""
                SELECT r.*, c.name as category_name
                FROM raw_uploads r
                JOIN categories c ON r.category_slug = c.slug
                WHERE r.category_slug = ? AND r.status = 'en_attente'
                ORDER BY r.uploaded_at ASC;
            """, (category_slug,))
        else:
            cursor.execute("""
                SELECT r.*, c.name as category_name
                FROM raw_uploads r
                JOIN categories c ON r.category_slug = c.slug
                WHERE r.status = 'en_attente'
                ORDER BY r.uploaded_at ASC;
            """)
        return [dict(row) for row in cursor.fetchall()]

def get_raw_upload_by_id(upload_id: int) -> Optional[Dict[str, Any]]:
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM raw_uploads WHERE id = ?;", (upload_id,))
        row = cursor.fetchone()
        return dict(row) if row else None

def update_raw_upload_status(upload_id: int, status: str):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("UPDATE raw_uploads SET status = ? WHERE id = ?;", (status, upload_id))
        conn.commit()

def delete_raw_upload(upload_id: int):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM raw_uploads WHERE id = ?;", (upload_id,))
        conn.commit()

def clear_all_raw_uploads(category_slug: Optional[str] = None):
    with get_db() as conn:
        cursor = conn.cursor()
        if category_slug:
            cursor.execute("DELETE FROM raw_uploads WHERE category_slug = ?;", (category_slug,))
        else:
            cursor.execute("DELETE FROM raw_uploads;")
        conn.commit()

# --- Processed Product Functions ---

def create_processed_product(category_slug: str, raw_upload_id: Optional[int], product_name: str, file_path: str, price: Optional[str] = "") -> Dict[str, Any]:
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO processed_products (category_slug, raw_upload_id, product_name, price, file_path)
            VALUES (?, ?, ?, ?, ?);
        """, (category_slug, raw_upload_id, product_name, price or "", file_path))
        conn.commit()
        product_id = cursor.lastrowid
        
        cursor.execute("SELECT * FROM processed_products WHERE id = ?;", (product_id,))
        return dict(cursor.fetchone())

def get_processed_products(category_slug: Optional[str] = None) -> List[Dict[str, Any]]:
    with get_db() as conn:
        cursor = conn.cursor()
        if category_slug:
            cursor.execute("""
                SELECT p.*, c.name as category_name, c.price as category_price
                FROM processed_products p
                JOIN categories c ON p.category_slug = c.slug
                WHERE p.category_slug = ?
                ORDER BY p.processed_at DESC;
            """, (category_slug,))
        else:
            cursor.execute("""
                SELECT p.*, c.name as category_name, c.price as category_price
                FROM processed_products p
                JOIN categories c ON p.category_slug = c.slug
                ORDER BY p.processed_at DESC;
            """)
        return [dict(row) for row in cursor.fetchall()]

def get_processed_product_by_id(product_id: int) -> Optional[Dict[str, Any]]:
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM processed_products WHERE id = ?;", (product_id,))
        row = cursor.fetchone()
        return dict(row) if row else None

def delete_processed_product(product_id: int):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM processed_products WHERE id = ?;", (product_id,))
        conn.commit()

def clear_all_processed_products(category_slug: Optional[str] = None):
    with get_db() as conn:
        cursor = conn.cursor()
        if category_slug:
            cursor.execute("DELETE FROM processed_products WHERE category_slug = ?;", (category_slug,))
        else:
            cursor.execute("DELETE FROM processed_products;")
        conn.commit()
