"""Tests for client_details and client_notes API endpoints."""

import pytest
import json
import sqlite3
import tempfile
import os
from app import create_app, init_db


@pytest.fixture
def app():
    """Create test app with a temporary file-based SQLite database."""
    # Create a temporary database file
    db_fd, db_path = tempfile.mkstemp(suffix=".db")
    os.close(db_fd)

    app = create_app()
    app.config["TESTING"] = True
    app.config["DB"] = db_path

    with app.app_context():
        # Override the global DB constant temporarily so init_db uses this path
        import app as app_module

        original_db = app_module.DB
        app_module.DB = db_path

        # Initialize schema
        init_db()

        # Insert test client into the same DB file
        with sqlite3.connect(db_path) as con:
            con.execute(
                "INSERT INTO client (id, id_canon, name) VALUES (1, '123456789', 'Test Client')"
            )
            con.commit()

        # Restore original DB constant
        app_module.DB = original_db

    yield app

    # Clean up DB file
    try:
        os.unlink(db_path)
    except Exception:
        pass


@pytest.fixture
def client(app):
    """Create test client."""
    return app.test_client()


def test_get_client_details_empty(client):
    """Test getting client details when none exist."""
    response = client.get('/api/client/123456789/details')
    assert response.status_code == 200
    
    data = json.loads(response.data)
    # When no explicit client_details row exists, API derives
    # first/last name from the full client name "Test Client".
    assert data['first_name'] == 'Test'
    assert data['last_name'] == 'Client'
    assert data['date_of_birth'] == ''
    assert data['email'] == ''
    assert data['employer'] == ''


def test_post_client_details(client):
    """Test creating/updating client details."""
    test_data = {
        'first_name': 'John',
        'last_name': 'Doe',
        'date_of_birth': '1990-01-01',
        'email': 'john.doe@example.com',
        'employer': 'Test Company'
    }
    
    response = client.post(
        '/api/client/123456789/details',
        data=json.dumps(test_data),
        content_type='application/json'
    )
    assert response.status_code == 200
    
    data = json.loads(response.data)
    assert data['status'] == 'ok'


def test_get_client_details_after_post(client):
    """Test getting client details after creating them."""
    # First create details
    test_data = {
        'first_name': 'Jane',
        'last_name': 'Smith',
        'date_of_birth': '1985-05-15',
        'email': 'jane.smith@example.com',
        'employer': 'Another Company'
    }
    
    client.post(
        '/api/client/123456789/details',
        data=json.dumps(test_data),
        content_type='application/json'
    )
    
    # Then get details
    response = client.get('/api/client/123456789/details')
    assert response.status_code == 200
    
    data = json.loads(response.data)
    assert data['first_name'] == 'Jane'
    assert data['last_name'] == 'Smith'
    assert data['date_of_birth'] == '1985-05-15'
    assert data['email'] == 'jane.smith@example.com'
    assert data['employer'] == 'Another Company'


def test_post_client_details_invalid_email(client):
    """Test posting client details with invalid email."""
    test_data = {
        'first_name': 'Test',
        'last_name': 'User',
        'email': 'invalid-email'
    }
    
    response = client.post(
        '/api/client/123456789/details',
        data=json.dumps(test_data),
        content_type='application/json'
    )
    assert response.status_code == 400
    
    data = json.loads(response.data)
    assert 'Invalid email format' in data['error']


def test_post_client_details_invalid_date(client):
    """Test posting client details with invalid date."""
    test_data = {
        'first_name': 'Test',
        'last_name': 'User',
        'date_of_birth': 'invalid-date'
    }
    
    response = client.post(
        '/api/client/123456789/details',
        data=json.dumps(test_data),
        content_type='application/json'
    )
    assert response.status_code == 400
    
    data = json.loads(response.data)
    assert 'Invalid date format' in data['error']


def test_delete_client_details(client):
    """Test deleting client details."""
    # First create details
    test_data = {
        'first_name': 'Delete',
        'last_name': 'Me',
        'email': 'delete@example.com'
    }
    
    client.post(
        '/api/client/123456789/details',
        data=json.dumps(test_data),
        content_type='application/json'
    )
    
    # Then delete them
    response = client.delete('/api/client/123456789/details')
    assert response.status_code == 200
    
    data = json.loads(response.data)
    assert data['status'] == 'ok'
    
    # Verify they're gone
    response = client.get('/api/client/123456789/details')
    data = json.loads(response.data)
    # After deleting client_details, API again falls back to
    # deriving names from the full client name "Test Client".
    assert data['first_name'] == 'Test'
    assert data['last_name'] == 'Client'
    assert data['email'] == ''


def test_client_not_found(client):
    """Test API with non-existent client."""
    response = client.get('/api/client/999999999/details')
    assert response.status_code == 404
    
    data = json.loads(response.data)
    assert 'Client not found' in data['error']


def test_update_partial_details(client):
    """Test updating only some fields."""
    # First create full details
    test_data = {
        'first_name': 'Original',
        'last_name': 'Name',
        'email': 'original@example.com',
        'employer': 'Original Company'
    }
    
    client.post(
        '/api/client/123456789/details',
        data=json.dumps(test_data),
        content_type='application/json'
    )
    
    # Then update only some fields
    update_data = {
        'first_name': 'Updated',
        'email': 'updated@example.com'
    }
    
    response = client.post(
        '/api/client/123456789/details',
        data=json.dumps(update_data),
        content_type='application/json'
    )
    assert response.status_code == 200
    
    # Verify partial update
    response = client.get('/api/client/123456789/details')
    data = json.loads(response.data)
    assert data['first_name'] == 'Updated'
    assert data['last_name'] == 'Name'  # Should remain unchanged
    assert data['email'] == 'updated@example.com'
    assert data['employer'] == 'Original Company'  # Should remain unchanged


def test_get_client_notes_empty(client):
    """When no notes exist for a client, the notes list should be empty."""
    response = client.get('/api/client/123456789/notes')
    assert response.status_code == 200

    data = json.loads(response.data)
    assert isinstance(data, list)
    assert data == []


def test_post_and_get_client_note(client):
    """Posting a note should store it with a created_at timestamp and be retrievable."""
    note_text = 'פגישה עם הלקוח בשבוע הבא'

    # Post new note
    response = client.post(
        '/api/client/123456789/notes',
        data=json.dumps({'note': note_text}),
        content_type='application/json',
    )
    assert response.status_code == 200

    data = json.loads(response.data)
    assert data['status'] == 'ok'
    assert data['note'] == note_text
    assert 'created_at' in data

    # Fetch notes list
    response = client.get('/api/client/123456789/notes')
    assert response.status_code == 200

    notes = json.loads(response.data)
    assert isinstance(notes, list)
    assert len(notes) == 1
    assert notes[0]['note'] == note_text
    assert 'created_at' in notes[0]


def test_post_client_note_validation(client):
    """Posting without note or with empty note should fail with 400."""
    # Missing note field
    response = client.post(
        '/api/client/123456789/notes',
        data=json.dumps({}),
        content_type='application/json',
    )
    assert response.status_code == 400

    # Empty note text
    response = client.post(
        '/api/client/123456789/notes',
        data=json.dumps({'note': '   '}),
        content_type='application/json',
    )
    assert response.status_code == 400


def test_client_notes_client_not_found(client):
    """Notes API should return 404 for non-existent client."""
    response = client.get('/api/client/999999999/notes')
    assert response.status_code == 404

    data = json.loads(response.data)
    assert 'Client not found' in data['error']


def test_post_client_note_with_reminder(client):
    """Posting a note with a valid reminder date should store it."""
    note_text = 'בדיקת תזכורת'
    reminder_date = '2099-01-01'

    response = client.post(
        '/api/client/123456789/notes',
        data=json.dumps({'note': note_text, 'reminder_at': reminder_date}),
        content_type='application/json',
    )
    assert response.status_code == 200

    data = json.loads(response.data)
    assert data['status'] == 'ok'
    assert data['note'] == note_text
    assert data['reminder_at'] == reminder_date

    # Verify via GET
    response = client.get('/api/client/123456789/notes')
    assert response.status_code == 200
    notes = json.loads(response.data)
    assert any(n['note'] == note_text and n['reminder_at'] == reminder_date for n in notes)


def test_post_client_note_invalid_reminder_date(client):
    """Invalid reminder date format should be rejected with 400."""
    response = client.post(
        '/api/client/123456789/notes',
        data=json.dumps({'note': 'בדיקה', 'reminder_at': '31-12-2099'}),
        content_type='application/json',
    )
    assert response.status_code == 400

    data = json.loads(response.data)
    assert 'Invalid reminder date format' in data['error']


def test_dismiss_client_note_reminder(client):
    """Dismissing a note should set dismissed_at and keep the note."""
    note_text = 'תזכורת לסגירה'
    reminder_date = '2099-01-01'

    # Create note with reminder
    response = client.post(
        '/api/client/123456789/notes',
        data=json.dumps({'note': note_text, 'reminder_at': reminder_date}),
        content_type='application/json',
    )
    assert response.status_code == 200
    data = json.loads(response.data)
    note_id = data['id']

    # Dismiss the reminder
    dismiss_response = client.post(f'/api/client/123456789/notes/{note_id}/dismiss')
    assert dismiss_response.status_code == 200
    dismiss_data = json.loads(dismiss_response.data)
    assert dismiss_data['status'] == 'ok'
    assert 'dismissed_at' in dismiss_data

    # Verify via GET that the note exists and has dismissed_at set
    get_response = client.get('/api/client/123456789/notes')
    assert get_response.status_code == 200
    notes = json.loads(get_response.data)

    matching = [n for n in notes if n['id'] == note_id]
    assert len(matching) == 1
    assert matching[0]['note'] == note_text
    assert matching[0]['reminder_at'] == reminder_date
    assert matching[0]['dismissed_at'] is not None
