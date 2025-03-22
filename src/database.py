import sqlite3

DB_NAME = "expenses.db"

def init_db():
    """Initialize the database and create the transactions table if not exists."""
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                amount REAL,
                category TEXT,
                description TEXT,
                date TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.commit()

def get_db_connection():
    """Helper function to connect to the database."""
    return sqlite3.connect(DB_NAME)

def add_expense_to_db(amount, category, description):
    """Insert a new expense into the database."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO transactions (amount, category, description, date) VALUES (?, ?, ?, DATE('now'))",
            (amount, category, description)
        )
        conn.commit()

def get_summary_from_db():
    """Retrieve total spending grouped by category."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT category, SUM(amount) FROM transactions GROUP BY category")
        return {row[0]: row[1] for row in cursor.fetchall()}

def check_budget_from_db():
    """Check if spending exceeds predefined budget categories."""
    budget = {
        "groceries": 200,
        "dining": 100,
        "transportation": 50,
        "other": 150
    }
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT category, SUM(amount) FROM transactions GROUP BY category")
        summary = {row[0]: row[1] for row in cursor.fetchall()}

    return [
        f"Warning: You exceeded your {category} budget by ${total - budget[category]:.2f}!"
        for category, total in summary.items() if category in budget and total > budget[category]
    ]
