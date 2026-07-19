# Database Layer Specification

## 1. Overview

Implement a complete SQLite database layer by replacing the placeholder implementation in `database/db.py`.

This database layer serves as the foundation of the Spendly application. Future modules—including authentication, user profiles, and expense tracking—will depend on this implementation.

---

## 2. Dependencies

This is the initial implementation and has no prerequisites.

---

## 3. API Routes

No new routes are required.

The existing placeholder routes in `app.py` should remain unchanged.

---

# 4. Database Schema

## Table: `users`

| Column | Type | Constraints |
|----------|------|-------------|
| `id` | INTEGER | PRIMARY KEY AUTOINCREMENT |
| `name` | TEXT | NOT NULL |
| `email` | TEXT | UNIQUE, NOT NULL |
| `password_hash` | TEXT | NOT NULL |
| `created_at` | TEXT | DEFAULT `datetime('now')` |

---

## Table: `expenses`

| Column | Type | Constraints |
|----------|------|-------------|
| `id` | INTEGER | PRIMARY KEY AUTOINCREMENT |
| `user_id` | INTEGER | FOREIGN KEY → `users(id)`, NOT NULL |
| `amount` | REAL | NOT NULL |
| `category` | TEXT | NOT NULL |
| `date` | TEXT | NOT NULL (`YYYY-MM-DD`) |
| `description` | TEXT | Nullable |
| `created_at` | TEXT | DEFAULT `datetime('now')` |

---

# 5. Required Functions (`database/db.py`)

## `get_db()`

Implement a function that:

- Opens a SQLite connection to `spendly.db` (or `expense_tracker.db`) in the project root.
- Sets:
  - `connection.row_factory = sqlite3.Row`
  - `PRAGMA foreign_keys = ON`
- Returns the configured connection.

---

## `init_db()`

Implement a function that:

- Creates both database tables using `CREATE TABLE IF NOT EXISTS`.
- Can be executed multiple times without errors.
- Ensures the database schema is initialized before the application starts.

---

## `seed_db()`

Implement a function that:

- Checks whether the `users` table already contains data.
- Returns immediately if data already exists (prevent duplicate seed data).
- Inserts one demo user:

| Field | Value |
|-------|-------|
| Name | Demo User |
| Email | demo@spendly.com |
| Password | demo123 (hashed using `werkzeug.security.generate_password_hash`) |

- Inserts **8 sample expenses** linked to the demo user.
- Expenses should:
  - Cover multiple categories.
  - Be spread across the current month.
  - Include at least one expense for each defined category.

---

# 6. Application Startup Changes

Update `app.py` to:

- Import:
  - `get_db`
  - `init_db`
  - `seed_db`
- Execute:

```python
with app.app_context():
    init_db()
    seed_db()
```

This ensures the database is initialized before any routes are used.

---

# 7. Files to Modify

| File | Required Changes |
|------|------------------|
| `database/db.py` | Implement database connection, schema creation, and seed logic |
| `app.py` | Import and initialize the database during startup |

---

# 8. New Files

No new files are required.

---

# 9. Dependencies

Do not introduce additional packages.

Use only:

- `sqlite3` (Python standard library)
- `werkzeug.security`

---

# 10. Allowed Expense Categories

Use **only** the following category values:

- Food
- Transport
- Bills
- Health
- Entertainment
- Shopping
- Other

---

# 11. Implementation Requirements

- Do **not** use an ORM (e.g., SQLAlchemy).
- Use **parameterized SQL queries only**.
- Never build SQL statements using string interpolation or formatting.
- Enable `PRAGMA foreign_keys = ON` for every database connection.
- Store monetary values as `REAL`.
- Hash passwords using:

```python
from werkzeug.security import generate_password_hash
```

- Ensure `seed_db()` never inserts duplicate records.
- Store all dates in `YYYY-MM-DD` format.

---

# 12. Expected Behavior

### `get_db()`

Should return a SQLite connection configured with:

- Dictionary-style row access (`sqlite3.Row`)
- Foreign key enforcement enabled

### `init_db()`

Should:

- Create both tables if they do not already exist.
- Execute safely on repeated application startups.

### `seed_db()`

Should:

- Insert demo data only once.
- Never duplicate records across multiple executions.

The database must enforce:

- Unique email addresses.
- Valid foreign key relationships between users and expenses.

---

# 13. Error Handling

- Duplicate email insertion → `UNIQUE` constraint error.
- Invalid `user_id` when inserting an expense → foreign key constraint error.
- Invalid SQL operations → raise appropriate SQLite exceptions for debugging.

---

# 14. Definition of Done

- [ ] Database file is automatically created on application startup.
- [ ] Both tables exist with the required schema and constraints.
- [ ] Demo user is created with a hashed password.
- [ ] Eight sample expenses are inserted.
- [ ] Seed data is inserted only once.
- [ ] Application starts without database errors.
- [ ] Foreign key constraints are enforced.
- [ ] All SQL statements use parameterized queries.
