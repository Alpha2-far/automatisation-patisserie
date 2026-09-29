# Graph Report - .  (2026-09-29)

## Corpus Check
- Corpus is ~32,414 words - fits in a single context window. You may not need a graph.

## Summary
- 125 nodes · 174 edges · 10 communities detected
- Extraction: 100% EXTRACTED · 0% INFERRED · 0% AMBIGUOUS
- Token cost: 0 input · 0 output
- Edge kinds: contains: 74 · calls: 53 · rationale_for: 35 · MODIFIES: 9 · inherits: 2 · ON_BRANCH: 1


## Input Scope
- Requested: auto
- Resolved: committed (source: default-auto)
- Included files: 18 · Candidates: 23
- Excluded: 7 untracked · 9715 ignored · 0 sensitive · 0 missing committed
- Recommendation: Use --scope all or graphify.yaml inputs.corpus for a knowledge-base folder.

## Graph Freshness
- Built from Git commit: `8519abd`
- Compare this hash to `git rev-parse HEAD` before trusting freshness-sensitive graph output.
## God Nodes (most connected - your core abstractions)
1. `get_db()` - 19 edges
2. `loadCategories()` - 11 edges
3. `showToast()` - 9 edges
4. `refreshIcons()` - 7 edges
5. `process_single_upload()` - 6 edges
6. `runAutomation()` - 6 edges
7. `create_category()` - 4 edges
8. `init_excel_workbook()` - 4 edges
9. `loadUploads()` - 4 edges
10. `loadProcessedProducts()` - 4 edges

## Surprising Connections (you probably didn't know these)
- None detected - all connections are within the same source files.

## Communities

### Community 0 - "Community 0"
Cohesion: 0.14
Nodes (25): clear_all_processed_products(), clear_all_raw_uploads(), create_category(), create_processed_product(), create_raw_upload(), delete_category_by_slug(), delete_processed_product(), delete_raw_upload() (+17 more)

### Community 1 - "Community 1"
Cohesion: 0.21
Nodes (18): deleteProcessedItem(), deleteUploadItem(), handleFilesUpload(), loadCategories(), loadProcessedProducts(), loadUploads(), openCategoryModal(), openLightbox() (+10 more)

### Community 2 - "Community 2"
Cohesion: 0.12
Nodes (14): main, 8519abd feat: initial release of Pâtisserie Studio web application with OpenCV auto-crop & price extraction, download_all_zip(), download_category_zip(), download_excel_registry(), Download ZIP archive of clean images for a specific category., Download master ZIP archive of all category folders and clean images., Download central Excel registry (catalogue_global.xlsx). (+6 more)

### Community 3 - "Community 3"
Cohesion: 0.23
Nodes (11): auto_crop_alpha(), batch_process_pending_uploads(), detect_product_photo_box(), get_processing_status(), get_rembg_session(), process_single_upload(), Process a single raw upload record., Batch process all pending (or all if pending empty) raw uploads with real-time s (+3 more)

### Community 4 - "Community 4"
Cohesion: 0.18
Nodes (10): clear_gallery(), get_status(), list_processed_products(), Trigger product photo cropping or background removal for pending uploads., Get real-time batch processing progress status., Retrieve processed products list., Clear all processed products for a category or globally., Delete a processed product from database and disk. (+2 more)

### Community 5 - "Community 5"
Cohesion: 0.20
Nodes (9): BaseModel, add_category(), CategoryCreateRequest, list_categories(), Retrieve all product categories with stats., Create a new category dynamically., Delete a category by slug., remove_category() (+1 more)

### Community 6 - "Community 6"
Cohesion: 0.22
Nodes (8): clear_raw_uploads_gallery(), delete_upload(), list_uploads(), Delete a raw upload file from disk and database., Multi-file upload handler for raw screenshots., Retrieve raw uploads list, optionally filtered by category., Delete all raw upload files for a category or globally., upload_files()

### Community 7 - "Community 7"
Cohesion: 0.29
Nodes (6): health_check(), lifespan(), Modern lifespan context manager for startup and shutdown events., Health check endpoint verifying database connectivity and storage readiness., Render main application dashboard., render_index()

### Community 8 - "Community 8"
Cohesion: 0.38
Nodes (6): append_to_excel_registry(), ensure_excel_registry_exists(), init_excel_workbook(), Creates a new openpyxl Workbook initialized with styled headers., Ensures that the catalogue_global.xlsx file exists with proper headers.     Retu, Appends a new processed product record to catalogue_final/catalogue_global.xlsx.

### Community 9 - "Community 9"
Cohesion: 0.67
Nodes (2): ensure_directories_exist(), Ensure that storage directories exist on disk.

## Knowledge Gaps
- **35 isolated node(s):** `Ensure that storage directories exist on disk.`, `Convert text to URL-safe slug stripping accents and special characters.`, `Extracts price from string (e.g. 'Gâteau d'anniversaire à 15000 francs').     Re`, `Return a database connection with dict-like row factory and foreign keys enabled`, `Initialize database schema with price columns.` (+30 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **Thin community `Community 9`** (2 nodes): `ensure_directories_exist()`, `Ensure that storage directories exist on disk.`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **What connects `Ensure that storage directories exist on disk.`, `Convert text to URL-safe slug stripping accents and special characters.`, `Extracts price from string (e.g. 'Gâteau d'anniversaire à 15000 francs').     Re` to the rest of the system?**
  _35 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `Community 0` be split into smaller, more focused modules?**
  _Cohesion score 0.13538461538461538 - nodes in this community are weakly interconnected._
- **Should `Community 2` be split into smaller, more focused modules?**
  _Cohesion score 0.11764705882352941 - nodes in this community are weakly interconnected._