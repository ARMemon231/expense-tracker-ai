import pytest
from flask import session
from expense_tracker.app import app
from expense_tracker.database.db import init_db, get_db
from expense_tracker.database.queries import get_expense_by_id, update_expense, insert_expense

@pytest.fixture
def client():
    app.config['TESTING'] = True
    app.config['SECRET_KEY'] = 'test_key'
    with app.test_client() as client:
        with app.app_context():
            init_db()
        yield client

@pytest.fixture
def user(client):
    # Create a test user
    from expense_tracker.database.db import create_user
    # Use a unique email for each test
    import uuid
    email = f"test_{uuid.uuid4().hex}@example.com"
    hashed_pw = "test_hash" # In real app, would use generate_password_hash
    user_id = create_user("Test User", email, hashed_pw)
    return {"id": user_id, "email": email}

@pytest.fixture
def expense(client, user):
    with app.app_context():
        with get_db() as db:
            insert_expense(db, user['id'], 100.0, "Food", "2026-08-01", "Test Lunch")
            # Get the last inserted id
            cursor = db.execute('SELECT id FROM expenses ORDER BY id DESC LIMIT 1')
            return cursor.fetchone()['id']

def test_get_expense_by_id_valid(user, expense):
    with app.app_context():
        res = get_expense_by_id(expense, user['id'])
        assert res is not None
        assert res['id'] == expense

def test_get_expense_by_id_wrong_user(user, expense):
    with app.app_context():
        # Create another user
        from expense_tracker.database.db import create_user
        create_user("Other", "other@example.com", "hash")
        # Find other user's id (just use 999 for simplicity as id is auto-inc)
        # Better yet, fetch the actual id
        with get_db() as db:
            other_user = db.execute('SELECT id FROM users WHERE email = "other@example.com"').fetchone()
            other_id = other_user['id']
            res = get_expense_by_id(expense, other_id)
            assert res is None

def test_update_expense_valid(user, expense):
    with app.app_context():
        with get_db() as db:
            update_expense(db, expense, user['id'], 150.0, "Transport", "2026-08-02", "Updated Ride")
            row = db.execute('SELECT * FROM expenses WHERE id = ?', (expense,)).fetchone()
            assert row['amount'] == 150.0
            assert row['category'] == "Transport"
            assert row['date'] == "2026-08-02"
            assert row['description'] == "Updated Ride"

def test_edit_expense_unauthenticated(client):
    response = client.get("/expenses/1/edit")
    assert response.status_code == 302
    assert "/login" in response.location

def test_edit_expense_get_valid(client, user, expense):
    with client.session_transaction() as sess:
        sess['user_id'] = user['id']

    response = client.get(f"/expenses/{expense}/edit")
    assert response.status_code == 200
    assert b"Edit Expense" in response.data
    assert b"100.0" in response.data # Original amount

def test_edit_expense_get_not_found(client, user):
    with client.session_transaction() as sess:
        sess['user_id'] = user['id']

    response = client.get("/expenses/9999/edit")
    assert response.status_code == 404

def test_edit_expense_post_success(client, user, expense):
    with client.session_transaction() as sess:
        sess['user_id'] = user['id']

    data = {
        "amount": "200.0",
        "category": "Health",
        "date": "2026-08-03",
        "description": "Updated Doctor"
    }
    response = client.post(f"/expenses/{expense}/edit", data=data)
    assert response.status_code == 302
    assert "/profile" in response.location

    with app.app_context():
        with get_db() as db:
            row = db.execute('SELECT * FROM expenses WHERE id = ?', (expense,)).fetchone()
            assert row['amount'] == 200.0
            assert row['category'] == "Health"
            assert row['date'] == "2026-08-03"
            assert row['description'] == "Updated Doctor"

def test_edit_expense_post_invalid_amount(client, user, expense):
    with client.session_transaction() as sess:
        sess['user_id'] = user['id']

    data = {
        "amount": "-10.0",
        "category": "Food",
        "date": "2026-08-01",
        "description": "Bad Amount"
    }
    response = client.post(f"/expenses/{expense}/edit", data=data)
    assert response.status_code == 200
    assert b"Amount must be a positive number" in response.data

def test_edit_expense_post_invalid_category(client, user, expense):
    with client.session_transaction() as sess:
        sess['user_id'] = user['id']

    data = {
        "amount": "50.0",
        "category": "InvalidCat",
        "date": "2026-08-01",
        "description": "Bad Cat"
    }
    response = client.post(f"/expenses/{expense}/edit", data=data)
    assert response.status_code == 200
    assert b"Please select a valid category" in response.data

def test_edit_expense_post_invalid_date(client, user, expense):
    with client.session_transaction() as sess:
        sess['user_id'] = user['id']

    data = {
        "amount": "50.0",
        "category": "Food",
        "date": "not-a-date",
        "description": "Bad Date"
    }
    response = client.post(f"/expenses/{expense}/edit", data=data)
    assert response.status_code == 200
    assert b"Invalid date format" in response.data

def test_edit_expense_post_blank_description(client, user, expense):
    with client.session_transaction() as sess:
        sess['user_id'] = user['id']

    data = {
        "amount": "50.0",
        "category": "Food",
        "date": "2026-08-01",
        "description": "   "
    }
    response = client.post(f"/expenses/{expense}/edit", data=data)
    assert response.status_code == 302

    with app.app_context():
        with get_db() as db:
            row = db.execute('SELECT description FROM expenses WHERE id = ?', (expense,)).fetchone()
            assert row['description'] is None
