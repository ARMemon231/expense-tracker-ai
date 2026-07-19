# Implementation Plan: Database Layer Specification

This plan outlines the implementation of the database layer for the Spendly application, as specified in `.claude/specs/01-Database_Layer_Specification.md`.

## Goals
- Implement a robust SQLite database layer without using an ORM.
- Ensure data integrity through schema constraints and foreign key enforcement.
- Provide a seamless developer experience via automated database initialization and seeding.

## Files to Modify
- `expense-tracker/database/db.py`: Implementation of core DB functions.
- `expense-tracker/app.py`: Integration of DB initialization into the Flask app startup.

## Implementation Details

### 1. Database Schema
Two tables will be created in `spendly.db`:
- **`users`**: `id` (PK), `name`, `email` (Unique), `password_hash`, `created_at`.
- **`expenses`**: `id` (PK), `user_id` (FK -> users), `amount` (REAL), `category`, `date` (YYYY-MM-DD), `description`, `created_at`.

### 2. Core Functions in `database/db.py`
- **`get_db()`**: 
    - Connect to `spendly.db`.
    - Set `row_factory = sqlite3.Row`.
    - Execute `PRAGMA foreign_keys = ON`.
- **`init_db()`**: 
    - Execute `CREATE TABLE IF NOT EXISTS` for both `users` and `expenses`.
- **`seed_db()`**: 
    - Check if `users` table is empty.
    - Insert a demo user (`demo@spendly.com`) with a hashed password using `werkzeug.security.generate_password_hash`.
    - Insert 8 sample expenses across the allowed categories: Food, Transport, Bills, Health, Entertainment, Shopping, Other.

### 3. App Integration in `app.py`
- Import `init_db` and `seed_db` from `database.db`.
- Wrap the initialization calls in `with app.app_context():` to ensure the database is ready before the first request.

## Verification Steps
- [ ] Run the application and verify `spendly.db` is created in the root directory.
- [ ] Use a SQLite browser or CLI to verify the schema and constraints.
- [ ] Verify that the demo user and 8 sample expenses exist.
- [ ] Restart the application multiple times to ensure `seed_db()` does not create duplicate records.
- [ ] Verify that foreign key constraints are working (e.g., trying to insert an expense for a non-existent user should fail).
- [ ] Confirm all SQL queries use `?` placeholders for parameterization.
