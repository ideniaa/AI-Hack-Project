import sqlite3
from datetime import datetime

# Function to connect to the database
def connect_db():
    return sqlite3.connect('database.db')

# Function to initialize the database (creating necessary tables)
def init_db():
    conn = connect_db()
    cursor = conn.cursor()

    # Table for storing expenses
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS expenses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            amount REAL NOT NULL,
            description TEXT NOT NULL,
            category TEXT,
            date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Table for tracking budgets
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS budgets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            category TEXT UNIQUE NOT NULL,
            limit_amount REAL NOT NULL,
            spent_amount REAL DEFAULT 0
        )
    ''')

    # Table for savings goals
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS savings_goals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            goal_name TEXT NOT NULL,
            target_amount REAL NOT NULL,
            current_savings REAL DEFAULT 0
        )
    ''')

    # Table for notifications/alerts
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS notifications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            message TEXT NOT NULL,
            status TEXT DEFAULT 'unread',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Create default budgets for main categories if they don't exist
    default_budgets = [
        ("food", 500),
        ("housing", 1500),
        ("transport", 300),
        ("entertainment", 200),
        ("shopping", 300),
        ("other", 200)
    ]
    
    for category, amount in default_budgets:
        cursor.execute('''
            INSERT OR IGNORE INTO budgets (category, limit_amount)
            VALUES (?, ?)
        ''', (category, amount))

    conn.commit()
    conn.close()

# Function to add an expense to the database
def add_expense(amount, description, category):
    conn = connect_db()
    cursor = conn.cursor()

    # Insert the expense into the database
    cursor.execute('''
        INSERT INTO expenses (amount, description, category) 
        VALUES (?, ?, ?)
    ''', (amount, description, category))

    # Check if the category has a budget entry
    cursor.execute('''
        SELECT * FROM budgets WHERE category = ?
    ''', (category,))
    
    budget_exists = cursor.fetchone()
    
    if budget_exists:
        # Update the spent amount in the budgets table for the respective category
        cursor.execute('''
            UPDATE budgets
            SET spent_amount = spent_amount + ?
            WHERE category = ?
        ''', (amount, category))
    else:
        # Create a default budget for this category
        cursor.execute('''
            INSERT INTO budgets (category, limit_amount, spent_amount)
            VALUES (?, ?, ?)
        ''', (category, 300, amount))  # Default budget of $300

    # Check if budget is exceeded and create notification if needed
    cursor.execute('''
        SELECT limit_amount, spent_amount FROM budgets WHERE category = ?
    ''', (category,))
    
    result = cursor.fetchone()
    if result:
        limit_amount, spent_amount = result
        if spent_amount > limit_amount:
            # Create a notification about exceeding budget
            cursor.execute('''
                INSERT INTO notifications (message, status)
                VALUES (?, 'unread')
            ''', (f"Alert: You've exceeded your {category} budget of ${limit_amount}!",))

    conn.commit()
    conn.close()

# Function to get the budget insights for a specific category
def get_budget_insights(category):
    conn = connect_db()
    cursor = conn.cursor()

    # Retrieve budget data for the category
    cursor.execute('''
        SELECT limit_amount, spent_amount FROM budgets WHERE category = ?
    ''', (category,))
    result = cursor.fetchone()

    if result:
        limit_amount, spent_amount = result
        remaining_budget = limit_amount - spent_amount
        advice = ""

        # Provide smart advice based on budget and spending
        if spent_amount > limit_amount:
            advice = "You've exceeded your budget in this category. Consider reducing your spending."
        elif remaining_budget < (limit_amount * 0.1):  # Less than 10% remaining
            advice = "You're close to reaching your budget limit. Keep an eye on your spending."
        elif remaining_budget < (limit_amount * 0.3):  # Less than 30% remaining
            advice = "You're using your budget well, but be mindful of upcoming expenses."
        else:
            advice = "You're well within your budget. Great financial management!"

        return {
            "category": category,
            "limit_amount": limit_amount,
            "spent_amount": spent_amount,
            "remaining_budget": remaining_budget,
            "advice": advice
        }
    else:
        return {"message": f"Budget for '{category}' not found. Please set a budget first."}

# Function to set a budget for a specific category
def set_budget(category, limit_amount):
    conn = connect_db()
    cursor = conn.cursor()

    # Check if the category already has a budget
    cursor.execute('''
        SELECT * FROM budgets WHERE category = ?
    ''', (category,))
    existing_budget = cursor.fetchone()

    if existing_budget:
        # If the budget already exists, update the limit_amount
        cursor.execute('''
            UPDATE budgets
            SET limit_amount = ?
            WHERE category = ?
        ''', (limit_amount, category))
    else:
        # If the budget doesn't exist, create a new budget for the category
        cursor.execute('''
            INSERT INTO budgets (category, limit_amount) 
            VALUES (?, ?)
        ''', (category, limit_amount))

    conn.commit()
    conn.close()

# Function to add a savings goal to the database
def add_savings_goal(goal_name, target_amount):
    conn = connect_db()
    cursor = conn.cursor()

    cursor.execute('''
        INSERT INTO savings_goals (goal_name, target_amount)
        VALUES (?, ?)
    ''', (goal_name, target_amount))

    conn.commit()
    conn.close()

# Function to update savings progress
def update_savings_goal(goal_name, current_savings):
    conn = connect_db()
    cursor = conn.cursor()

    cursor.execute('''
        UPDATE savings_goals 
        SET current_savings = ?
        WHERE goal_name = ?
    ''', (current_savings, goal_name))

    conn.commit()
    conn.close()

# Function to get notification
def get_notifications(limit=5):
    conn = connect_db()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT id, message, created_at FROM notifications
        WHERE status = 'unread'
        ORDER BY created_at DESC
        LIMIT ?
    ''', (limit,))
    
    notifications = cursor.fetchall()
    result = [{"id": n[0], "message": n[1], "date": n[2]} for n in notifications]
    
    conn.close()
    return result

if __name__ == '__main__':
    init_db()
    print("Database initialized successfully.")
