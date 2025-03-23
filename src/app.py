from flask import Flask, request, jsonify
from chatbot import chatbot_response  # Importing the chatbot logic from chatbot.py
from database import connect_db, add_expense, get_budget_insights, set_budget, init_db  # Import the init_db function

app = Flask(__name__)

# Initialize the database before the first request in modern Flask
# Instead of @app.before_first_request which is deprecated
with app.app_context():
    init_db()
    print("Database initialized successfully.")

# Categorize expense (Basic AI/Rule-Based)
def categorize_expense(description):
    categories = {
        "food": ["groceries", "restaurant", "snack", "food", "lunch", "dinner", "breakfast"],
        "housing": ["rent", "mortgage", "utilities", "electricity", "water", "gas bill", "internet"],
        "transport": ["gas", "uber", "bus", "car", "taxi", "train", "subway", "lyft"],
        "entertainment": ["movie", "game", "concert", "theater", "netflix", "subscription"],
        "shopping": ["clothes", "electronics", "shoes", "amazon", "online", "mall"]
    }
    
    description = description.lower()
    for category, keywords in categories.items():
        if any(keyword in description for keyword in keywords):
            return category
    
    return "other"  # Default category if no match

# Add expense to the database
@app.route('/add_expense', methods=['POST'])
def add_expense_route():
    data = request.json
    amount = data.get("amount")
    description = data.get("description")
    category = data.get("category")
    
    # If category not provided, auto-categorize
    if not category:
        category = categorize_expense(description)

    # Call the database function to add expense
    add_expense(amount, description, category)

    return jsonify({"message": f"Expense of ${amount} added under {category} category."})

# Parse expense command from natural language
def parse_expense_command(message):
    # Simple parsing for expressions like "Add $50 for groceries"
    if "add" in message.lower() and "$" in message:
        parts = message.split("$")
        if len(parts) > 1:
            # Extract amount
            amount_part = parts[1].split()[0].strip()
            try:
                amount = float(amount_part.replace(',', ''))
                
                # Extract description
                desc_parts = message.lower().split("for")
                if len(desc_parts) > 1:
                    description = desc_parts[1].strip()
                    return {"amount": amount, "description": description}
            except ValueError:
                pass
    return None

# Retrieve budget insights
@app.route('/get_budget', methods=['GET', 'POST'])
def get_budget_route():
    if request.method == 'POST':
        data = request.json
        category = data.get("category")
    else:
        category = request.args.get("category")

    # Call the database function to get budget insights
    budget_info = get_budget_insights(category)

    return jsonify(budget_info)

# Set a budget for a category
@app.route('/set_budget', methods=['POST'])
def set_budget_route():
    data = request.json
    category = data.get("category")
    limit_amount = data.get("limit_amount")

    # Call the database function to set the budget
    set_budget(category, limit_amount)

    return jsonify({"message": f"Budget for {category} set to ${limit_amount}."})

# API endpoint for chatbot interaction
@app.route('/chat', methods=['POST'])
def chat():
    data = request.json
    user_message = data.get("message", "")
    
    # Check if this is an expense command
    expense_data = parse_expense_command(user_message)
    if expense_data:
        category = categorize_expense(expense_data["description"])
        add_expense(expense_data["amount"], expense_data["description"], category)
        return jsonify({
            "response": f"I've added your expense of ${expense_data['amount']} for {expense_data['description']} under the {category} category."
        })
    
    # Check if user is asking about budget
    if "budget" in user_message.lower() and "for" in user_message.lower():
        category = user_message.lower().split("budget for")[-1].strip().rstrip('?')
        budget_info = get_budget_insights(category)
        
        if "message" in budget_info:
            return jsonify({"response": budget_info["message"]})
        else:
            response = f"Budget for {category}: ${budget_info['limit_amount']}. " \
                      f"You've spent ${budget_info['spent_amount']}, with ${budget_info['remaining_budget']} remaining. " \
                      f"{budget_info['advice']}"
            return jsonify({"response": response})
    
    # For other messages, use the standard chatbot response
    response = chatbot_response(user_message)
    return jsonify({"response": response})

if __name__ == '__main__':
    app.run(debug=True)
