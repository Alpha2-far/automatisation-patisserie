import pytest
from app.db import (
    slugify,
    parse_price,
    get_db,
    create_category,
    get_all_categories,
    get_category_by_slug,
    delete_category_by_slug,
    create_raw_upload,
    get_raw_uploads,
    delete_raw_upload,
    create_processed_product,
    get_processed_products,
    delete_processed_product
)

def test_slugify():
    assert slugify("Gâteau d'anniversaire !") == "gateau_danniversaire"
    assert slugify("Éclair au Café - Spécial") == "eclair_au_cafe_special"
    assert slugify("   Mille-feuille   ") == "mille_feuille"

def test_parse_price():
    name, price = parse_price("Gâteau d'anniversaire à 15000 francs")
    assert name == "Gâteau d'anniversaire"
    assert price == "15 000 FCFA"

    name2, price2 = parse_price("Fraisier 25000 FCFA")
    assert name2 == "Fraisier"
    assert price2 == "25 000 FCFA"

    name3, price3 = parse_price("Croissant pur beurre")
    assert name3 == "Croissant pur beurre"
    assert price3 == ""

def test_category_lifecycle(isolated_env):
    # Create category with price auto-extracted
    cat = create_category("Gâteau Chocolat à 10000 francs")
    assert cat["name"] == "Gâteau Chocolat"
    assert cat["price"] == "10 000 FCFA"
    assert "10000" in cat["slug"]

    # Verify physical upload directory was created
    upload_dir = isolated_env["uploads_dir"] / cat["slug"]
    assert upload_dir.exists()

    # Retrieve
    retrieved = get_category_by_slug(cat["slug"])
    assert retrieved is not None
    assert retrieved["name"] == "Gâteau Chocolat"

    # Try duplicate slug creation
    with pytest.raises(ValueError):
        create_category("Gâteau Chocolat à 10000 francs")

    # Add raw upload and processed product
    raw = create_raw_upload(
        filename="test_img.png",
        original_filename="original.png",
        category_slug=cat["slug"],
        file_path=f"uploads_bruts/{cat['slug']}/test_img.png",
        file_size=1024
    )
    assert raw["id"] is not None

    processed = create_processed_product(
        category_slug=cat["slug"],
        raw_upload_id=raw["id"],
        product_name="clean_product.png",
        file_path=f"catalogue_final/{cat['slug']}/clean_product.png",
        price=cat["price"]
    )
    assert processed["id"] is not None

    # Delete category and verify cascade + directory cleanup
    delete_category_by_slug(cat["slug"])
    assert get_category_by_slug(cat["slug"]) is None
    assert len(get_raw_uploads(cat["slug"])) == 0
    assert len(get_processed_products(cat["slug"])) == 0
    assert not upload_dir.exists()
