# Spec: Registration

## Overview
The Registration feature allows new users to create an account in the Spendly expense tracker. This is a critical early stage of the roadmap, as it establishes the user identity required for personalized expense tracking. Users will provide their name, email, and password to create a secure account.

## Depends on
- 01-Database_Layer_Specification

## Routes
- `GET /register` — Display the registration form — public
- `POST /register` — Handle account creation — public

## Database changes
No database changes. The `users` table already contains the necessary fields (`name`, `email`, `password_hash`).

## Templates
- **Create:** `expense-tracker/templates/register.html`
- **Modify:** `expense-tracker/templates/base.html` (ensure navigation links to register/login are present)

## Files to change
- `expense-tracker/app.py` (implement registration logic)

## Files to create
- `expense-tracker/templates/register.html`

## New dependencies
No new dependencies.

## Rules for implementation
- No SQLAlchemy or ORMs
- Parameterised queries only
- Passwords hashed with werkzeug
- Use CSS variables — never hardcode hex values
- All templates extend `base.html`

## Definition of done
- [ ] User can navigate to `/register` and see a registration form.
- [ ] User can successfully create an account by providing a name, email, and password.
- [ ] Account creation is prevented if any field is missing.
- [ ] Account creation is prevented if the email is already registered (displays appropriate error message).
- [ ] Passwords are stored as hashes in the database, not as plain text.
- [ ] After successful registration, the user is redirected to the login page with a success message.
