import pytest
from datetime import datetime, timedelta
from app import app as flask_app
from database.db import init_db

@pytest.fixture
def app():
    flask_app.config.update({
        'TESTING': True,
        'DATABASE': ':memory:',
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
    # Register a test user
    client.post('/register', data={'name': 'Test User', 'email': 'test@example.com', 'password': 'testpass', 'confirm_password': 'testpass'})
    # Login
    client.post('/login', data={'email': 'test@example.com', 'password': 'testpass'})
    return client

def insert_expense(client, amount, category, date, description="Test"):
    """Helper to insert expenses into the DB for the current session user."""
    from database.db import get_db
    with flask_app.app_context():
        conn = get_db()
        # Find the user_id of the logged-in user
        user = conn.execute('SELECT id FROM users LIMIT 1').fetchone()
        user_id = user['id']
        conn.execute(
            'INSERT INTO expenses (user_id, amount, category, date, description) VALUES (?, ?, ?, ?, ?)',
            (user_id, amount, category, date, description)
        )
        conn.commit()

class TestDateFilterProfile:

    def test_profile_auth_guard(self, client):
        """Unauthenticated users should be redirected to login."""
        response = client.get('/profile')
        assert response.status_code == 302
        assert b'/login' in response.location

    def test_profile_no_filter_shows_all(self, auth_client):
        """Visiting /profile without params shows all expenses."""
        insert_expense(auth_client, 100.0, 'Food', '2026-01-01')
        insert_expense(auth_client, 200.0, 'Bills', '2026-07-01')

        response = auth_client.get('/profile')
        assert response.status_code == 200
        assert b'Rs 300.00' in response.data
        assert b'Food' in response.data
        assert b'Bills' in response.data

    def test_profile_valid_date_range_filter(self, auth_client):
        """Valid date_from and date_to filter data correctly."""
        insert_expense(auth_client, 100.0, 'Food', '2026-01-01') # Out of range
        insert_expense(auth_client, 200.0, 'Bills', '2026-07-10') # In range
        insert_expense(auth_client, 300.0, 'Health', '2026-07-20') # In range
        insert_expense(auth_client, 400.0, 'Other', '2026-08-01') # Out of range

        # Filter for July 2026
        response = auth_client.get('/profile?date_from=2026-07-01&date_to=2026-07-31')

        assert response.status_code == 200
        assert b'Rs 500.00' in response.data # 200 + 300
        assert b'Bills' in response.data
        assert b'Health' in response.data
        assert b'Food' not in response.data
        assert b'Other' not in response.data

    def test_profile_malformed_date_falls_back(self, auth_client):
        """Malformed date strings should fall back to 'All Time' view."""
        insert_expense(auth_client, 100.0, 'Food', '2026-01-01')

        response = auth_client.get('/profile?date_from=not-a-date&date_to=2026-12-31')

        assert response.status_code == 200
        assert b'Rs 100.00' in response.data # Should still show the expense

    def test_profile_invalid_range_flashes_error(self, auth_client):
        """date_from > date_to should flash error and show all expenses."""
        insert_expense(auth_client, 100.0, 'Food', '2026-01-01')

        response = auth_client.get('/profile?date_from=2026-12-31&date_to=2026-01-01')

        assert response.status_code == 200
        assert b'Start date must be before end date.' in response.data
        assert b'Rs 100.00' in response.data

    def test_profile_partial_dates_falls_back(self, auth_client):
        """Providing only one of the date parameters should fall back to 'All Time'."""
        insert_expense(auth_client, 100.0, 'Food', '2026-01-01')

        response = auth_client.get('/profile?date_from=2026-01-01')
        assert response.status_code == 200
        assert b'Rs 100.00' in response.data

    def test_profile_no_expenses_in_range(self, auth_client):
        """Range with no expenses should show zero values without error."""
        insert_expense(auth_client, 100.0, 'Food', '2026-01-01')

        response = auth_client.get('/profile?date_from=2026-02-01&date_to=2026-02-28')

        assert response.status_code == 200
        assert b'Rs 0.00' in response.data
        assert b'0 transactions' in response.data

    @pytest.mark.parametrize("preset_params", [
        {"date_from": "2026-07-01", "date_to": "2026-07-31"}, # Simulating 'This Month' for July 2026
    ])
    def test_profile_preset_logic_structure(self, auth_client, preset_params):
        """Verify that the profile route accepts preset-like parameters."""
        insert_expense(auth_client, 100.0, 'Food', '2026-07-15')

        response = auth_client.get(f'/profile?date_from={preset_params["date_from"]}&date_to={preset_params["date_to"]}')
        assert response.status_code == 200
        assert b'Rs 100.00' in response.data
