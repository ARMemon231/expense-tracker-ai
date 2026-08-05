import pytest
from app import app
from database.db import get_db, init_db
from database.queries import delete_expense, get_expense_by_id
from flask import session

@pytest.fixture
def app_context():
    with app.app_context():
        init_db()
        with get_db() as db:
            # Clear existing data to ensure a clean state
            db.execute('DELETE FROM expenses')
            db.execute('DELETE FROM users')

            # Create two users
            cursor = db.execute(
                'INSERT INTO users (name, email, password_hash, created_at) VALUES (?, ?, ?, ?)',
                ('User One', 'one@example.com', 'hash1', '2026-01-01 00:00:00')
            )
            user1_id = cursor.lastrowid

            cursor = db.execute(
                'INSERT INTO users (name, email, password_hash, created_at) VALUES (?, ?, ?, ?)',
                ('User Two', 'two@example.com', 'hash2', '2026-01-01 00:00:00')
            )
            user2_id = cursor.lastrowid

            # Create an expense for User One
            cursor = db.execute(
                'INSERT INTO expenses (user_id, amount, category, date, description) VALUES (?, ?, ?, ?, ?)',
                (user1_id, 100.0, 'Food', '2026-08-01', 'Test Lunch')
            )
            expense_id = cursor.lastrowid
            db.commit()
        yield {
            "user1_id": user1_id,
            "user2_id": user2_id,
            "expense_id": expense_id
        }

@pytest.fixture
def client(app_context):
    return app.test_client()

# --- Unit Tests for delete_expense ---

def test_delete_expense_success(app_context):
    with get_db() as db:
        delete_expense(db, app_context["expense_id"], app_context["user1_id"])
        row = db.execute('SELECT * FROM expenses WHERE id = ?', (app_context["expense_id"],)).fetchone()
        assert row is None

def test_delete_expense_wrong_user(app_context):
    with get_db() as db:
        # Expense belongs to User 1, try deleting as User 2
        delete_expense(db, app_context["expense_id"], app_context["user2_id"])
        row = db.execute('SELECT * FROM expenses WHERE id = ?', (app_context["expense_id"],)).fetchone()
        assert row is not None

def test_delete_expense_nonexistent(app_context):
    with get_db() as db:
        delete_expense(db, 999, app_context["user1_id"])
        row = db.execute('SELECT * FROM expenses WHERE id = ?', (app_context["expense_id"],)).fetchone()
        assert row is not None

# --- Route Tests ---

def test_delete_route_unauthenticated(client):
    # No session set
    response = client.post('/expenses/1/delete')
    assert response.status_code == 302
    assert '/login' in response.location

def test_delete_route_method_not_allowed(client):
    response = client.get('/expenses/1/delete')
    assert response.status_code == 405

def test_delete_route_unauthorized(client, app_context):
    with client.session_transaction() as sess:
        sess['user_id'] = app_context["user2_id"]

    response = client.post(f'/expenses/{app_context["expense_id"]}/delete')
    assert response.status_code == 404

def test_delete_route_success(client, app_context):
    with client.session_transaction() as sess:
        sess['user_id'] = app_context["user1_id"]

    response = client.post(f'/expenses/{app_context["expense_id"]}/delete')
    assert response.status_code == 302
    assert '/profile' in response.location

    with app.app_context():
        with get_db() as db:
            row = db.execute('SELECT * FROM expenses WHERE id = ?', (app_context["expense_id"],)).fetchone()
            assert row is None
