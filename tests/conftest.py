import os
import shutil
import tempfile
from pathlib import Path
import pytest
from fastapi.testclient import TestClient

import app.config as config
import app.db as db_mod
import app.services.excel as excel_mod
import app.services.exporter as exporter_mod
import app.services.processor as processor_mod
from app.main import app

@pytest.fixture(autouse=True)
def isolated_env(monkeypatch, tmp_path):
    """Sets up an isolated environment with temporary database and storage folders."""
    test_db = tmp_path / "test_database.db"
    test_uploads = tmp_path / "test_uploads_bruts"
    test_catalogue = tmp_path / "test_catalogue_final"
    test_excel = test_catalogue / "catalogue_global.xlsx"

    test_uploads.mkdir(parents=True, exist_ok=True)
    test_catalogue.mkdir(parents=True, exist_ok=True)

    monkeypatch.setattr(config, "DB_PATH", test_db)
    monkeypatch.setattr(config, "UPLOADS_BRUTS_DIR", test_uploads)
    monkeypatch.setattr(config, "CATALOGUE_FINAL_DIR", test_catalogue)

    monkeypatch.setattr(db_mod, "DB_PATH", test_db)
    monkeypatch.setattr(db_mod, "UPLOADS_BRUTS_DIR", test_uploads)
    monkeypatch.setattr(db_mod, "CATALOGUE_FINAL_DIR", test_catalogue)

    monkeypatch.setattr(excel_mod, "CATALOGUE_FINAL_DIR", test_catalogue)
    monkeypatch.setattr(excel_mod, "EXCEL_PATH", test_excel)

    monkeypatch.setattr(exporter_mod, "CATALOGUE_FINAL_DIR", test_catalogue)

    monkeypatch.setattr(processor_mod, "UPLOADS_BRUTS_DIR", test_uploads)
    monkeypatch.setattr(processor_mod, "CATALOGUE_FINAL_DIR", test_catalogue)

    db_mod.init_db()
    excel_mod.ensure_excel_registry_exists()

    yield {
        "tmp_path": tmp_path,
        "db_path": test_db,
        "uploads_dir": test_uploads,
        "catalogue_dir": test_catalogue,
        "excel_path": test_excel
    }

@pytest.fixture
def client():
    """Provides a TestClient wrapped with FastAPI lifespan context."""
    with TestClient(app) as test_client:
        yield test_client
