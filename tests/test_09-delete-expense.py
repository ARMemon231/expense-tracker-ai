import pytest
from flask import url_for
from app import app as flask_app
from database.db import init_db, get_db
from database.queries import delete_expense, insert_expense, get_expense_by_id

@pytest.fixture
def app():
    flask_app.config.update({
        'TESTING': True,
        'SECRET_KEY': 'test-secret',
        'WTF_CSRF_ENABLED': False,
    })

    with flask_app.app_context():
        init_db()
        yield flask_app

@pytest.fixture
def client(app):
    return app.test_client()

@pytest.fixture
def auth_client(client):
    """A test client that is already logged in."""
    # Register user
    client.post('/register', data={
        'name': 'testuser',
        'email': 'test@example.com',
        'password': 'testpass',
        'confirm_password': 'testpass'
    })
    # Login user
    client.post('/login', data={
        'email': 'test@example.com',
        'password': 'testpass'
    })
    return client

@pytest.fixture
def setup_data(app):
    """Helper to insert expenses for different users."""
    def _setup(user_id, amount=10.0, category="Food", date="2026-01-01", desc="Test"):
        with app.app_context():
            with get_db() as db:
                insert_expense(db, user_id, amount, category, date, desc)
                return db.execute('SELECT last_insert_rowid()').fetchone()[0]
    return _setup

class TestDeleteExpenseUnit:
    """Unit tests for the delete_expense database helper."""

    def test_delete_expense_success(self, app, setup_data):
        with app.app_context():
            with get_db() as db:
                # Setup: Create user
                db.execute('INSERT INTO users (name, email, password_hash, created_at) VALUES (?, ?, ?, ?)',
                           ('User 1', 'u1@ex.com', 'hash', '2026-01-01 00:00:00'))
                u1_id = db.execute('SELECT last_insert_rowid()').fetchone()[0]

                exp_id = setup_data(u1_id)

                # Action: Delete correctly
                delete_expense(db, exp_id, u1_id)

                # Assert: Row is gone
                row = db.execute('SELECT * FROM expenses WHERE id = ?', (exp_id,)).fetchone()
                assert row is None, "Expense should have been deleted"

    def test_delete_expense_wrong_user(self, app, setup_data):
        with app.app_context():
            with get_db() as db:
                # Setup: Create two users
                db.execute('INSERT INTO users (name, email, password_hash, created_at) VALUES (?, ?, ?, ?)',
                           ('User 1', 'u1@ex.com', 'hash', '2026-01-01 00:00:00'))
                u1_id = db.execute('SELECT last_insert_rowid()').fetchone()[0]
                db.execute('INSERT INTO users (name, email, password_hash, created_at) VALUES (?, ?, ?, ?)',
                           ('User 2', 'u2@ex.com', 'hash', '2026-01-01 00:00:00'))
                u2_id = db.execute('SELECT last_insert_rowid()').fetchone()[0]

                exp_id = setup_data(u1_id) # Expense belongs to User 1

                # Action: User 2 tries to delete User 1's expense
                delete_expense(db, exp_id, u2_id)

                # Assert: Row still exists
                row = db.execute('SELECT * FROM expenses WHERE id = ?', (exp_id,)).fetchone()
                assert row is not None, "Expense should NOT be deleted by a different user"

    def test_delete_expense_non_existent(self, app):
        with app.app_context():
            with get_db() as db:
                # Should not raise error
                delete_expense(db, 9999, 1)

class TestDeleteExpenseRoute:
    """Integration tests for the POST /expenses/<id>/delete route."""

    def test_delete_unauthenticated(self, client):
        response = client.post('/expenses/1/delete')
        assert response.status_code == 302
        assert response.location == '/login'

    def test_delete_method_not_allowed(self, auth_client):
        # Using GET instead of POST
        response = auth_client.get('/expenses/1/delete')
        assert response.status_code == 405

    def test_delete_own_expense_success(self, auth_client, app, setup_data):
        with app.app_context():
            # Get the logged in user's ID
            user = get_db().execute('SELECT id FROM users WHERE email = ?', ('test@example.com',)).fetchone()
            user_id = user['id']
            exp_id = setup_data(user_id)

            # Action: Delete own expense
            response = auth_client.post(f'/expenses/{exp_id}/delete')

            # Assert: Redirect to profile
            assert response.status_code == 302
            assert response.location == '/profile'

            # Assert: Database is updated
            with get_db() as db:
                row = db.execute('SELECT * FROM expenses WHERE id = ?', (exp_id,)).fetchone()
                assert row is None, "Expense should be removed from DB"

    def test_delete_other_user_expense_404(self, auth_client, app, setup_data):
        with app.app_context():
            # Setup: Create a second user and an expense for them
            with get_db() as db:
                db.execute('INSERT INTO users (name, email, password_hash, created_at) VALUES (?, ?, ?, ?)',
                           ('Other User', 'other@example.com', 'hash', '2026-01-01 00:00:00'))
                other_id = db.execute('SELECT last_insert_rowid()').fetchone()[0]

            other_exp_id = setup_data(other_id)

            # Action: Logged-in user attempts to delete other user's expense
            response = auth_client.post(f'/expenses/{other_exp_id}/delete')

            # Assert: 404 Not Found
            assert response.status_code == 404

            # Assert: Expense still exists
            with get_db() as db:
                row = db.execute('SELECT * FROM expenses WHERE id = ?', (other_exp_id,)).fetchone()
                assert row is not None, "Other user's expense should still exist"

    def test_delete_non_existent_expense_404(self, auth_client):
        # Using a very high ID that won't exist
        response = auth_client.post('/expenses/99999/delete')
        assert response.status_code == 404
