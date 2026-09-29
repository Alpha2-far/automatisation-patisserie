import io
from PIL import Image

def test_health_check(client):
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["database"] == "connected"
    assert data["uploads_dir"] is True
    assert data["catalogue_dir"] is True
    assert data["version"] == "1.1.0"

def test_render_index(client):
    response = client.get("/")
    assert response.status_code == 200
    assert "Pâtisserie Studio" in response.text

def test_categories_api(client):
    # List categories (initially empty)
    res = client.get("/api/categories")
    assert res.status_code == 200
    assert isinstance(res.json(), list)

    # Create category
    res = client.post("/api/categories", json={
        "name": "Brioches Moelleuses à 8000 FCFA",
        "price": None
    })
    assert res.status_code == 201
    cat = res.json()["category"]
    assert cat["name"] == "Brioches Moelleuses"
    assert cat["price"] == "8 000 FCFA"
    slug = cat["slug"]

    # Duplicate creation error
    res_dup = client.post("/api/categories", json={
        "name": "Brioches Moelleuses à 8000 FCFA"
    })
    assert res_dup.status_code == 400

    # Delete category
    res_del = client.delete(f"/api/categories/{slug}")
    assert res_del.status_code == 200

    # Check 404 on deleting non-existent
    res_del404 = client.delete(f"/api/categories/{slug}")
    assert res_del404.status_code == 404

def test_export_excel_endpoint(client):
    """Test that downloading the Excel registry succeeds even if no products were processed."""
    res = client.get("/api/export/excel")
    assert res.status_code == 200
    assert res.headers["content-type"] == "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"

def test_export_zip_endpoint(client):
    res = client.get("/api/export/zip")
    assert res.status_code == 200
    assert res.headers["content-type"] == "application/zip"

def test_upload_and_process_status(client):
    # Create category first
    res = client.post("/api/categories", json={"name": "Cupcakes Délices"})
    slug = res.json()["category"]["slug"]

    # Generate a dummy test image in memory
    img = Image.new("RGB", (100, 100), color="pink")
    img_byte_arr = io.BytesIO()
    img.save(img_byte_arr, format="PNG")
    img_byte_arr.seek(0)

    # Upload test image
    res = client.post(
        "/api/uploads",
        data={"category_slug": slug},
        files={"files": ("test_cupcake.png", img_byte_arr, "image/png")}
    )
    assert res.status_code == 201
    upload_data = res.json()
    assert upload_data["success"] is True
    assert upload_data["uploaded_count"] == 1

    # Check process status
    res = client.get("/api/process/status")
    assert res.status_code == 200
    assert "is_processing" in res.json()
