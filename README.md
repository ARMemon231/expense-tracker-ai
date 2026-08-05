# 💰 Spendly — AI Expense Tracker

A smart, full-stack expense tracking web application built with Flask and SQLite. Track your spending, visualize category breakdowns, and stay on top of your finances.

## ✨ Features

- **User Authentication** — Secure registration & login with hashed passwords
- **Dashboard** — View total spending, transaction count, and top category at a glance
- **Expense Management** — Add, edit, and delete expenses with category tagging
- **Category Breakdown** — See how your spending distributes across categories (Food, Transport, Bills, Health, Entertainment, Shopping, Other)
- **Date Filtering** — Filter transactions by custom date range or presets (This Month, Last 3 Months, Last 6 Months, All Time)
- **Analytics Page** — Dedicated analytics view for deeper insights
- **Responsive UI** — Clean, modern templates with Jinja2

## 🛠️ Tech Stack

| Layer      | Technology           |
|------------|----------------------|
| Backend    | Python, Flask        |
| Database   | SQLite               |
| Templating | Jinja2               |
| Auth       | Werkzeug (password hashing) |
| Server     | Gunicorn (production) |
| Testing    | Pytest, pytest-flask  |

## 📁 Project Structure

```
expense-tracker/
├── expense_tracker/
│   ├── app.py                 # Main Flask application & routes
│   ├── requirements.txt       # Python dependencies
│   ├── database/
│   │   ├── db.py              # Database initialization & seeding
│   │   └── queries.py         # SQL query functions
│   ├── static/                # CSS, JS, images
│   └── templates/             # Jinja2 HTML templates
│       ├── base.html          # Base layout
│       ├── landing.html       # Landing page
│       ├── login.html         # Login form
│       ├── register.html      # Registration form
│       ├── profile.html       # User dashboard
│       ├── add_expense.html   # Add expense form
│       ├── edit_expense.html  # Edit expense form
│       ├── analytics.html     # Analytics page
│       ├── terms.html         # Terms of service
│       └── privacy.html       # Privacy policy
├── tests/                     # Test suite
└── README.md
```

## 🚀 Getting Started

### Prerequisites

- Python 3.9+

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/ARMemon231/expense-tracker-ai.git
   cd expense-tracker-ai
   ```

2. **Create a virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate        # macOS/Linux
   venv\Scripts\activate           # Windows
   ```

3. **Install dependencies**
   ```bash
   pip install -r expense_tracker/requirements.txt
   ```

4. **Run the app**
   ```bash
   cd expense_tracker
   python app.py
   ```

5. **Open in browser**
   ```
   http://localhost:5001
   ```

### Running Tests

```bash
pytest
```

## ☁️ Deploy on Render

1. Push your code to GitHub
2. Create a new **Web Service** on [Render](https://render.com)
3. Connect your GitHub repo
4. Configure the following settings:

   | Setting         | Value                          |
   |-----------------|--------------------------------|
   | **Runtime**     | Python                         |
   | **Root Directory** | `expense_tracker`           |
   | **Build Command** | `pip install -r requirements.txt` |
   | **Start Command** | `gunicorn app:app`           |

5. Click **Deploy** 🚀

## 📄 License

This project is open source and available under the [MIT License](LICENSE).
