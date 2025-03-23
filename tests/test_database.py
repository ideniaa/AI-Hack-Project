import sqlite3
import os

def inspect_database():
    """Inspect the contents of the SQLite database"""
    database_path = "../src/database.db"  # Navigate up one level then into src

    # Check if database file exists
    if not os.path.exists(database_path ):
        print("Database file not found. Run the application first.")
        return
    
    # Connect to the database
    conn = sqlite3.connect(database_path)
    cursor = conn.cursor()
    
    # List all tables
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()
    print("\n=== Database Tables ===")
    for table in tables:
        print(f"- {table[0]}")
    
    # Inspect expenses table
    print("\n=== Expenses Table ===")
    cursor.execute("SELECT * FROM expenses")
    expenses = cursor.fetchall()
    if expenses:
        print(f"Found {len(expenses)} expense records:")
        for expense in expenses[:5]:  # Show up to 5 records
            print(f"  ID: {expense[0]}, Amount: ${expense[1]}, Description: '{expense[2]}', Category: '{expense[3]}', Date: {expense[4]}")
        if len(expenses) > 5:
            print(f"  ... and {len(expenses) - 5} more")
    else:
        print("No expenses found")
    
    # Inspect budgets table
    print("\n=== Budgets Table ===")
    cursor.execute("SELECT * FROM budgets")
    budgets = cursor.fetchall()
    if budgets:
        print(f"Found {len(budgets)} budget records:")
        for budget in budgets:
            print(f"  Category: '{budget[1]}', Limit: ${budget[2]}, Spent: ${budget[3]}")
    else:
        print("No budgets found")
    
    # Inspect notifications
    print("\n=== Notifications Table ===")
    cursor.execute("SELECT * FROM notifications")
    notifications = cursor.fetchall()
    if notifications:
        print(f"Found {len(notifications)} notifications:")
        for notif in notifications[:5]:
            print(f"  ID: {notif[0]}, Message: '{notif[1]}', Status: {notif[2]}")
        if len(notifications) > 5:
            print(f"  ... and {len(notifications) - 5} more")
    else:
        print("No notifications found")
    
    # Close connection
    conn.close()

if __name__ == "__main__":
    inspect_database()