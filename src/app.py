"""
What this does:
Sets up an API to log expenses
Auto-categorizes transactions based on keywords
Stores data in an SQLite database

"""
from flask import Flask, request, jsonify
import sqlite3

app = Flask(__name__)


# Initialize database
def init_db():
    conn = sqlite3.connect("expenses.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            amount REAL,
            category TEXT,
            description TEXT,
            date TEXT
        )
    """)
    conn.commit()
    conn.close()

init_db()


# Add expenses
@app.route("/add_expense", methods=["POST"])
def add_expense():
    data = request.json
    amount = data.get("amount")
    description = data.get("description")
    category = categorize_expense(description)  # auto-categorization

    conn = sqlite3.connect("expense.db")
    cursor = conn.cursor()
    cursor.execute("INSERT INTO transactions (amount, category, description, date) VALUES (?, ?, ?, DATE('now'))",
                   (amount, category, description))
    conn.commit()
    conn.close()

    return jsonify({"message": "Expense added", "category": category})

def categorize_expense(description):
    keywords = {
        "groceries": ["supermarket", "walmart", "grocery", "food"],
        "dining": ["restaurant", "cafe", "diner", "lunch"],
        "transportation": ["uber", "gas", "subway", "train", "bus"],
        "entertainment": ["movie", "netflix", "concert", "game"]
    }
    for category, words in keywords.items():
        if any(word in description.lower() for word in words):
            return category
    return "other"


# Retrieve user spending
@app.route("/get_summary", methods=["GET"])
def get_summary():
    conn = sqlite3.connect("expense.db")
    cursor = conn.cursor()
    cursor.execute("SELECT category, SUM(amount) FROM transactions GROUP BY category")
    summary = cursor.fetchall()
    conn.close()

    return jsonify({category: total for category, total in summary})


# Warn user if they overspend
@app.route("/check_budget", methods=["GET"])
def check_budget():
    budget = {"groceries": 200, "dining": 100, "transportation": 50}    # Set budgets

    conn = sqlite3.connect("expenses.db")
    cursor = conn.cursor()
    cursor.execute("SELECT category, SUM(amount) FROM transportation GROUP BY category")
    summary = {category: total for category, total in cursor.fetchall()}

    alerts = []
    for category, total in summary.items():
        if category in budget and total > budget[category]:
            alerts.append(f"Warning: You exceeded your {category} budget by ${total - budget[category]:.2f}!")

            return jsonify({"alerts": alerts})


if __name__ == "__main__":
    app.run(debug=True)
