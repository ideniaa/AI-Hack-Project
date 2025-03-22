from flask import Flask, request, jsonify, render_template
from database import init_db, add_expense_to_db, get_summary_from_db, check_budget_from_db
from chatbot import get_chatbot_response

app = Flask(__name__)

# Initialize database
init_db()

# Home page route (serves chatbot UI)
@app.route("/")
def home():
    return render_template("index.html")

# Add an expense
@app.route("/add_expense", methods=["POST"])
def add_expense():
    data = request.get_json()
    amount = data.get("amount")
    description = data.get("description")

    if not amount or not description:
        return jsonify({"error": "Amount and description are required!"}), 400

    category = categorize_expense(description)
    add_expense_to_db(amount, category, description)

    return jsonify({"message": "Expense added", "category": category})

# Categorization logic
def categorize_expense(description):
    keywords = {
        "groceries": ["supermarket", "walmart", "grocery", "food"],
        "dining": ["restaurant", "cafe", "diner", "lunch", "coffee"],
        "transportation": ["uber", "gas", "subway", "train", "bus"],
        "entertainment": ["movie", "netflix", "concert", "game"]
    }
    for category, words in keywords.items():
        if any(word in description.lower() for word in words):
            return category
    return "other"

# Retrieve user spending summary
@app.route("/get_summary", methods=["GET"])
def get_summary():
    return jsonify(get_summary_from_db())

# Check if budget is exceeded
@app.route("/check_budget", methods=["GET"])
def check_budget():
    return jsonify({"alerts": check_budget_from_db()})

# Chatbot for expense-related queries
@app.route("/chatbot", methods=["POST"])
def chatbot():
    data = request.get_json()
    user_input = data.get("query", "")

    if not user_input:
        return jsonify({"error": "Query is required!"}), 400

    return jsonify({"response": get_chatbot_response(user_input)})

if __name__ == "__main__":
    app.run(debug=True, port=5001)
