import random
from database import get_budget_insights, set_budget, add_expense, connect_db

# Sample financial chatbot responses
RESPONSES = {
    "greeting": ["Hello! How can I help you with your finances today?", "Hi there! Need help with budgeting or expenses?"],
    "expense_tracking": ["You can add an expense by saying 'Add $50 for groceries'.", "Tracking expenses is easy! Just tell me what you spent and how much."],
    "budgeting": ["Setting a budget helps you save. Would you like to set one now?", "Tell me your budget goal, and I'll help you stick to it."],
    "savings": ["Saving is important! I can help you set savings goals.", "Want tips on saving money? Let's plan your financial future."],
    "help": ["Here are things I can do:\n- Add expenses (e.g., 'Add $45 for groceries')\n- Check budgets (e.g., 'What's my budget for food?')\n- Set budgets (e.g., 'Set budget for entertainment to $200')\n- Provide savings advice"],
    "default": ["I'm here to help! Ask me anything about your finances.", "Could you rephrase that? I want to assist you better."]
}

# Parse budget setting command
def parse_budget_command(message):
    if "set budget" in message.lower() or "set a budget" in message.lower():
        message = message.lower()
        if "for" in message and "to" in message:
            # Extract category and amount
            split_for = message.split("for")[1]
            category_part = split_for.split("to")[0].strip()
            amount_part = split_for.split("to")[1].strip()
            
            # Remove dollar sign if present
            if "$" in amount_part:
                amount_part = amount_part.replace("$", "")
            
            try:
                amount = float(amount_part.replace(',', ''))
                return {"category": category_part, "amount": amount}
            except ValueError:
                pass
    return None

# Enhanced chatbot logic with database integration
def chatbot_response(user_input):
    user_input = user_input.lower()
    
    # Check for greetings
    if any(word in user_input for word in ["hello", "hi", "hey"]):
        return random.choice(RESPONSES["greeting"])
    
    # Check for help request
    if "help" in user_input or "what can you do" in user_input:
        return random.choice(RESPONSES["help"])
    
    # Check for budget setting command
    budget_command = parse_budget_command(user_input)
    if budget_command:
        set_budget(budget_command["category"], budget_command["amount"])
        return f"I've set your budget for {budget_command['category']} to ${budget_command['amount']}."
    
    # Check for budget queries
    if "budget" in user_input and "for" in user_input:
        category = user_input.split("budget for")[-1].strip().rstrip('?')
        budget_info = get_budget_insights(category)
        
        if "message" in budget_info:
            return budget_info["message"]
        else:
            return f"Budget for {category}: ${budget_info['limit_amount']}. " \
                   f"You've spent ${budget_info['spent_amount']}, with ${budget_info['remaining_budget']} remaining. " \
                   f"{budget_info['advice']}"
    
    # Check for expense tracking questions
    if any(word in user_input for word in ["expense", "spending", "track"]):
        return random.choice(RESPONSES["expense_tracking"])
    
    # Check for savings advice
    if any(word in user_input for word in ["save", "saving", "savings"]):
        return random.choice(RESPONSES["savings"])
    
    # Get spending insights
    if "how much" in user_input and "spend" in user_input:
        conn = connect_db()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT SUM(amount) as total FROM expenses
        ''')
        result = cursor.fetchone()
        conn.close()
        
        if result and result[0]:
            return f"You've spent a total of ${result[0]:.2f} across all categories."
        else:
            return "You haven't recorded any expenses yet."
    
    # Default response
    return random.choice(RESPONSES["default"])
