"""Tests for the /upload/ route.

Covers basic GET rendering and a simple error case for POST
without a file.
"""
import pytest
import tempfile
import os
from pathlib import Path
import sys

# Add the parent directory to the path so we can import from the project
sys.path.insert(0, str(Path(__file__).parent.parent))

from app import create_app, init_db


@pytest.fixture
def app():
    """Create and configure a test app for upload tests."""
    # Create a temporary database file
    db_fd, db_path = tempfile.mkstemp(suffix=".db")
    os.close(db_fd)

    app = create_app()
    app.config["TESTING"] = True
    app.config["DB"] = db_path

    with app.app_context():
        # Override the DB constant temporarily for init_db
        import app as app_module
        original_db = app_module.DB
        app_module.DB = db_path

        # Initialize the test database
        init_db()

        # Ensure required routes are registered on this app instance
        app.add_url_rule("/", view_func=app_module.index)
        app.add_url_rule("/clients/", view_func=app_module.clients)
        app.add_url_rule("/upload/", view_func=app_module.upload, methods=["GET", "POST"])
        app.add_url_rule("/dashboard/", view_func=app_module.dashboard)

        # Restore original DB
        app_module.DB = original_db

    yield app

    # Clean up
    try:
        os.unlink(db_path)
    except Exception:
        pass


@pytest.fixture
def client(app):
    """Create a test client."""
    return app.test_client()


def test_upload_get(client):
    """GET /upload/ should return 200 and render the page."""
    res = client.get("/upload/")
    assert res.status_code == 200


def test_upload_post_without_file(client):
    """POST /upload/ without a file should return a clear error."""
    res = client.post("/upload/", data={"snap_date": "2025-07-01"})
    assert res.status_code == 400

    json_data = res.get_json()
    assert json_data is not None
    assert "error" in json_data
    assert "לא נבחר קובץ" in json_data["error"]
