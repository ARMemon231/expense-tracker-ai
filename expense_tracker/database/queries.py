from database.db import get_db
from datetime import datetime

def get_user_by_id(user_id):
    """
    Retrieves user info and formats joined date as 'Month YYYY'.
    """
    with get_db() as conn:
        row = conn.execute('SELECT name, email, created_at FROM users WHERE id = ?', (user_id,)).fetchone()
        if not row:
            return None

        # Format created_at (YYYY-MM-DD HH:MM:SS) to "Month YYYY"
        try:
            dt = datetime.strptime(row['created_at'], '%Y-%m-%d %H:%M:%S')
            member_since = dt.strftime('%B %Y')
        except (ValueError, TypeError):
            member_since = "Unknown"

        return {
            "name": row['name'],
            "email": row['email'],
            "member_since": member_since
        }

def insert_expense(db, user_id, amount, category, date, description):
    """
    Inserts a new expense record.
    description should be None if blank.
    """
    desc = description if description and description.strip() else None
    query = 'INSERT INTO expenses (user_id, amount, category, date, description) VALUES (?, ?, ?, ?, ?)'
    db.execute(query, (user_id, amount, category, date, desc))
    db.commit()

def get_summary_stats(user_id, date_from=None, date_to=None):
    """
    Calculates total spend, transaction count, and identifying the top category.
    """
    with get_db() as conn:
        query_parts = ['SELECT SUM(amount) as total, COUNT(*) as count FROM expenses WHERE user_id = ?']
        params = [user_id]

        if date_from and date_to:
            query_parts.append('AND date BETWEEN ? AND ?')
            params.extend([date_from.isoformat() if hasattr(date_from, 'isoformat') else date_from,
                           date_to.isoformat() if hasattr(date_to, 'isoformat') else date_to])

        stats = conn.execute(' '.join(query_parts), params).fetchone()

        total_spent = stats['total'] if stats['total'] is not None else 0.0
        tx_count = stats['count'] if stats['count'] is not None else 0

        # Top category
        cat_query_parts = ['SELECT category FROM expenses WHERE user_id = ?']
        cat_params = [user_id]

        if date_from and date_to:
            cat_query_parts.append('AND date BETWEEN ? AND ?')
            cat_params.extend([date_from.isoformat() if hasattr(date_from, 'isoformat') else date_from,
                               date_to.isoformat() if hasattr(date_to, 'isoformat') else date_to])

        cat_query = ' '.join(cat_query_parts) + ' GROUP BY category ORDER BY SUM(amount) DESC LIMIT 1'
        top_cat_row = conn.execute(cat_query, cat_params).fetchone()

        top_category = top_cat_row['category'] if top_cat_row else "—"

        return {
            "total_spent": total_spent,
            "transaction_count": tx_count,
            "top_category": top_category
        }

def get_recent_transactions(user_id, limit=10, date_from=None, date_to=None):
    """
    Returns the most recent expenses for the user.
    """
    with get_db() as conn:
        query_parts = ['SELECT id, date, description, category, amount FROM expenses WHERE user_id = ?']
        params = [user_id]

        if date_from and date_to:
            query_parts.append('AND date BETWEEN ? AND ?')
            params.extend([date_from.isoformat() if hasattr(date_from, 'isoformat') else date_from,
                           date_to.isoformat() if hasattr(date_to, 'isoformat') else date_to])

        query = ' '.join(query_parts) + ' ORDER BY date DESC LIMIT ?'
        params.append(limit)

        rows = conn.execute(query, params).fetchall()

        return [
            {
                "id": row['id'],
                "date": row['date'],
                "desc": row['description'],
                "category": row['category'],
                "amount": row['amount']
            }
            for row in rows
        ]

def get_category_breakdown(user_id, date_from=None, date_to=None):
    """
    Calculates spending per category with integer percentages summing to 100.
    """
    with get_db() as conn:
        # Get totals per category
        query_parts = ['SELECT category, SUM(amount) as total FROM expenses WHERE user_id = ?']
        params = [user_id]

        if date_from and date_to:
            query_parts.append('AND date BETWEEN ? AND ?')
            params.extend([date_from.isoformat() if hasattr(date_from, 'isoformat') else date_from,
                           date_to.isoformat() if hasattr(date_to, 'isoformat') else date_to])

        query = ' '.join(query_parts) + ' GROUP BY category ORDER BY total DESC'
        rows = conn.execute(query, params).fetchall()

        if not rows:
            return []

        grand_total = sum(row['total'] for row in rows)
        if grand_total == 0:
            return []

        # Calculate precise percentages and initial rounded values
        breakdown = []
        for row in rows:
            precise_pct = (row['total'] / grand_total) * 100
            breakdown.append({
                "name": row['category'],
                "amount": row['total'],
                "precise_pct": precise_pct,
                "pct": round(precise_pct)
            })

        # Rounding correction (Largest Remainder Method simplified)
        current_sum = sum(item['pct'] for item in breakdown)
        diff = 100 - current_sum

        if diff != 0:
            # Adjust the largest category to absorb the difference
            breakdown[0]['pct'] += diff

        # Remove helper field before returning
        for item in breakdown:
            item.pop('precise_pct')

        return breakdown

def get_expense_by_id(expense_id, user_id):
    """
    Fetches a single expense row only if it belongs to the given user.
    Returns None if not found or doesn't belong to user.
    """
    with get_db() as conn:
        row = conn.execute(
            'SELECT id, amount, category, date, description FROM expenses WHERE id = ? AND user_id = ?',
            (expense_id, user_id)
        ).fetchone()
        return row

def update_expense(db, expense_id, user_id, amount, category, date, description):
    """
    Updates an expense record.
    Ensures ownership with user_id in WHERE clause.
    description should be None if blank.
    """
    desc = description if description and description.strip() else None
    query = 'UPDATE expenses SET amount = ?, category = ?, date = ?, description = ? WHERE id = ? AND user_id = ?'
    db.execute(query, (amount, category, date, desc, expense_id, user_id))
    db.commit()

def delete_expense(db, expense_id, user_id):
    """
    Permanently deletes an expense record if it belongs to the given user.
    """
    query = 'DELETE FROM expenses WHERE id = ? AND user_id = ?'
    db.execute(query, (expense_id, user_id))
    db.commit()
