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

if __name__ == "__main__":
    app.run(debug=True)
