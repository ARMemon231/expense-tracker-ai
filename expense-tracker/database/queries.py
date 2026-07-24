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

def get_summary_stats(user_id):
    """
    Calculates total spend, transaction count, and identifying the top category.
    """
    with get_db() as conn:
        # Total spend and count
        stats = conn.execute(
            'SELECT SUM(amount) as total, COUNT(*) as count FROM expenses WHERE user_id = ?',
            (user_id,)
        ).fetchone()

        total_spent = stats['total'] if stats['total'] is not None else 0.0
        tx_count = stats['count'] if stats['count'] is not None else 0

        # Top category
        top_cat_row = conn.execute(
            'SELECT category FROM expenses WHERE user_id = ? GROUP BY category ORDER BY SUM(amount) DESC LIMIT 1',
            (user_id,)
        ).fetchone()

        top_category = top_cat_row['category'] if top_cat_row else "—"

        return {
            "total_spent": total_spent,
            "transaction_count": tx_count,
            "top_category": top_category
        }

def get_recent_transactions(user_id, limit=10):
    """
    Returns the most recent expenses for the user.
    """
    with get_db() as conn:
        rows = conn.execute(
            'SELECT date, description, category, amount FROM expenses WHERE user_id = ? ORDER BY date DESC LIMIT ?',
            (user_id, limit)
        ).fetchall()

        return [
            {
                "date": row['date'],
                "desc": row['description'],
                "category": row['category'],
                "amount": row['amount']
            }
            for row in rows
        ]

def get_category_breakdown(user_id):
    """
    Calculates spending per category with integer percentages summing to 100.
    """
    with get_db() as conn:
        # Get totals per category
        rows = conn.execute(
            'SELECT category, SUM(amount) as total FROM expenses WHERE user_id = ? GROUP BY category ORDER BY total DESC',
            (user_id,)
        ).fetchall()

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
