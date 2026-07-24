import pytest
from flask import Flask, session
from expense_tracker.database.queries import (
    get_user_by_id,
    get_summary_stats,
    get_recent_transactions,
    get_category_breakdown
)
from expense_tracker.database.db import init_db, get_db

@pytest.fixture
def app():
    app = Flask(__name__)
    app.config['TESTING'] = True
    app.config['SECRET_KEY'] = 'test_key'
    return app

@pytest.fixture
def setup_db():
    # In this project's current structure, init_db uses a fixed DB_PATH.
    # For tests, we ensure the DB is initialized.
    init_db()

    # Seed a test user and specific expenses for deterministic testing
    with get_db() as conn:
        conn.execute('DELETE FROM expenses')
        conn.execute('DELETE FROM users')

        cursor = conn.execute(
            'INSERT INTO users (name, email, password_hash, created_at) VALUES (?, ?, ?, ?)',
            ('Test User', 'test@example.com', 'hashed_pw', '2026-01-01 12:00:00')
        )
        user_id = cursor.lastrowid

        # 8 expenses, 7 categories, total = 346.24
        expenses = [
            (user_id, 15.50, 'Food', '2026-07-01', 'Lunch'),
            (user_id, 45.00, 'Transport', '2026-07-02', 'Fuel'),
            (user_id, 120.00, 'Bills', '2026-07-03', 'Electricity'), # Top Category
            (user_id, 30.00, 'Health', '2026-07-05', 'Pharmacy'),
            (user_id, 60.00, 'Entertainment', '2026-07-10', 'Movie'),
            (user_id, 25.00, 'Shopping', '2026-07-12', 'T-shirt'),
            (user_id, 10.00, 'Other', '2026-07-15', 'Misc'),
            (user_id, 40.74, 'Food', '2026-07-18', 'Coffee'),
        ]
        conn.executemany(
            'INSERT INTO expenses (user_id, amount, category, date, description) VALUES (?, ?, ?, ?, ?)',
            expenses
        )
        conn.commit()

    return user_id

def test_get_user_by_id(setup_db):
    user_id = setup_db
    user = get_user_by_id(user_id)
    assert user['name'] == 'Test User'
    assert user['email'] == 'test@example.com'
    assert user['member_since'] == 'January 2026'

    assert get_user_by_id(999) is None

def test_get_summary_stats(setup_db):
    user_id = setup_db
    stats = get_summary_stats(user_id)
    assert stats['total_spent'] == 346.24
    assert stats['transaction_count'] == 8
    assert stats['top_category'] == 'Bills'

def test_get_summary_stats_empty():
    # Test user with no expenses
    with get_db() as conn:
        cursor = conn.execute('INSERT INTO users (name, email, password_hash) VALUES (?, ?, ?)',
                             ('Empty', 'empty@ex.com', 'pw'))
        user_id = cursor.lastrowid

    stats = get_summary_stats(user_id)
    assert stats['total_spent'] == 0.0
    assert stats['transaction_count'] == 0
    assert stats['top_category'] == '—'

def test_get_recent_transactions(setup_db):
    user_id = setup_db
    txs = get_recent_transactions(user_id, limit=5)
    assert len(txs) == 5
    # Check ordering (most recent first)
    assert txs[0]['date'] == '2026-07-18'
    assert txs[-1]['date'] == '2026-07-05'

def test_get_category_breakdown(setup_db):
    user_id = setup_db
    breakdown = get_category_breakdown(user_id)

    assert len(breakdown) == 7
    # Sum of percentages must be exactly 100
    assert sum(item['pct'] for item in breakdown) == 100
    # Highest amount should be first
    assert breakdown[0]['name'] == 'Bills'

def test_get_category_breakdown_empty():
    with get_db() as conn:
        cursor = conn.execute('INSERT INTO users (name, email, password_hash) VALUES (?, ?, ?)',
                             ('Empty', 'empty2@ex.com', 'pw'))
        user_id = cursor.lastrowid

    assert get_category_breakdown(user_id) == []
