from flask import Flask, render_template, request, redirect, url_for, flash, session
from werkzeug.security import generate_password_hash, check_password_hash
from database.db import init_db, seed_db, create_user, get_user_by_email
from database.queries import get_user_by_id, get_summary_stats, get_recent_transactions, get_category_breakdown

app = Flask(__name__)
app.secret_key = "spendly_secret_key_for_flashing"

with app.app_context():
    init_db()
    seed_db()

app = Flask(__name__)
app.secret_key = "spendly_secret_key_for_flashing"

with app.app_context():
    init_db()
    seed_db()


# ------------------------------------------------------------------ #
# Routes                                                              #
# ------------------------------------------------------------------ #

@app.route("/")
def landing():
    return render_template("landing.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    if session.get("user_id"):
        return redirect(url_for("landing"))

    if request.method == "POST":
        name = request.form.get("name")
        email = request.form.get("email")
        password = request.form.get("password")
        confirm_password = request.form.get("confirm_password")

        if not name or not email or not password or not confirm_password:
            flash("All fields are required", "error")
            return render_template("register.html")

        if password != confirm_password:
            flash("Passwords do not match", "error")
            return render_template("register.html")

        hashed_pw = generate_password_hash(password)
        user_id = create_user(name, email, hashed_pw)

        if user_id is None:
            flash("Email already registered", "error")
            return render_template("register.html")

        flash("Account created successfully! Please sign in to continue.", "success")
        return redirect(url_for("login"))

    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if session.get("user_id"):
        return redirect(url_for("landing"))

    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")

        if not email or not password:
            flash("All fields are required", "error")
            return render_template("login.html")

        user = get_user_by_email(email)
        if user and check_password_hash(user["password_hash"], password):
            session["user_id"] = user["id"]
            return redirect(url_for("profile"))

        flash("Invalid email or password.", "error")
        return render_template("login.html")

    return render_template("login.html")


@app.route("/terms")
def terms():
    return render_template("terms.html")


@app.route("/privacy")
def privacy():
    return render_template("privacy.html")


# ------------------------------------------------------------------ #
# Placeholder routes — students will implement these                  #
# ------------------------------------------------------------------ #

@app.route("/logout")
def logout():
    session.clear()
    flash("You have been logged out.", "success")
    return redirect(url_for("landing"))


@app.route("/profile")
def profile():
    if not session.get("user_id"):
        flash("Please log in to access your profile.", "error")
        return redirect(url_for("login"))

    user_id = session["user_id"]

    # Fetch dynamic data from queries.py
    user_info = get_user_by_id(user_id)
    if not user_info:
        flash("User profile not found.", "error")
        return redirect(url_for("login"))

    stats = get_summary_stats(user_id)
    txs = get_recent_transactions(user_id)
    cats = get_category_breakdown(user_id)

    # Format data for the template
    profile_data = {
        "user": {
            "name": user_info["name"],
            "email": user_info["email"],
            "initials": "".join([n[0].upper() for n in user_info["name"].split()]),
            "joined": user_info["member_since"]
        },
        "stats": {
            "total_spent": f"Rs {stats['total_spent']:,.2f}",
            "tx_count": stats["transaction_count"],
            "top_category": stats["top_category"]
        },
        "transactions": [
            {
                "date": tx["date"],
                "desc": tx["desc"],
                "category": tx["category"],
                "amount": f"Rs {tx['amount']:,.2f}"
            }
            for tx in txs
        ],
        "categories": [
            {
                "name": cat["name"],
                "amount": f"Rs {cat['amount']:,.2f}",
                "percent": cat["pct"]
            }
            for cat in cats
        ]
    }
    return render_template("profile.html", profile=profile_data)


@app.route("/expenses/add")
def add_expense():
    return "Add expense — coming in Step 7"


@app.route("/expenses/<int:id>/edit")
def edit_expense(id):
    return "Edit expense — coming in Step 8"


@app.route("/expenses/<int:id>/delete")
def delete_expense(id):
    return "Delete expense — coming in Step 9"


if __name__ == "__main__":
    app.run(debug=True, port=5001)
