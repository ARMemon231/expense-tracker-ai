from flask import Flask, render_template, request, redirect, url_for, flash, session, send_from_directory
from werkzeug.security import generate_password_hash, check_password_hash
from database.db import init_db, seed_db, create_user, get_user_by_email
from database.queries import get_user_by_id, get_summary_stats, get_recent_transactions, get_category_breakdown
from datetime import datetime, timedelta

app = Flask(__name__)
app.secret_key = "spendly_secret_key_for_flashing"

with app.app_context():
    init_db()
    seed_db()


# ------------------------------------------------------------------ #
# Routes                                                              #
# ------------------------------------------------------------------ #

@app.route("/favicon.ico")
def favicon():
    return send_from_directory(app.static_folder, "favicon.svg", mimetype="image/svg+xml")


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

@app.route("/analytics")
def analytics():
    if not session.get("user_id"):
        flash("Please log in to access analytics.", "error")
        return redirect(url_for("login"))
    return render_template("analytics.html")


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

    # Date filter handling
    date_from = request.args.get("date_from")
    date_to = request.args.get("date_to")

    validated_from = None
    validated_to = None

    if date_from and date_to:
        try:
            validated_from = datetime.strptime(date_from, "%Y-%m-%d").date()
            validated_to = datetime.strptime(date_to, "%Y-%m-%d").date()

            if validated_from > validated_to:
                flash("Start date must be before end date.", "error")
                validated_from = validated_to = None
        except ValueError:
            validated_from = validated_to = None # Explicitly reset


    # Current date for preset calculations
    today = datetime.now().date()

    # Presets
    presets = {
        "this_month": {
            "label": "This Month",
            "from": datetime(today.year, today.month, 1).date(),
            "to": today
        },
        "last_3_months": {
            "label": "Last 3 Months",
            "from": today - timedelta(days=90), # Approx 3 months
            "to": today
        },
        "last_6_months": {
            "label": "Last 6 Months",
            "from": today - timedelta(days=180), # Approx 6 months
            "to": today
        },
        "all_time": {
            "label": "All Time",
            "from": None,
            "to": None
        }
    }

    # Fetch dynamic data from queries.py with date filters
    user_info = get_user_by_id(user_id)
    if not user_info:
        flash("User profile not found.", "error")
        return redirect(url_for("login"))

    stats = get_summary_stats(user_id, date_from=validated_from, date_to=validated_to)
    txs = get_recent_transactions(user_id, date_from=validated_from, date_to=validated_to)
    cats = get_category_breakdown(user_id, date_from=validated_from, date_to=validated_to)

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
    return render_template("profile.html", profile=profile_data, date_from=validated_from, date_to=validated_to, presets=presets)


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
