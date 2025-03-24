import os
import json
import pandas as pd
from flask import Flask, render_template, request, jsonify, session, redirect, url_for
import google.generativeai as genai
from dotenv import load_dotenv
from datetime import datetime
import sqlite3
#import plotly.express as px
import traceback  # For error tracking

# Load environment variables
load_dotenv()

# Configure Gemini API
api_key = os.getenv("GEMINI_API_KEY")
if api_key:
    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-2.0-flash')
        print("Gemini API configured successfully")
    except Exception as e:
        print(f"Warning: Failed to configure Gemini API: {str(e)}")
        model = None
else:
    model = None
    print("Warning: GEMINI_API_KEY not found in .env file")

# Initialize system prompt with financial advisor context
SYSTEM_PROMPT = """
You are AIWealth, a helpful and knowledgeable financial advisor chatbot. Your goal is to provide personalized financial guidance based on users' situations.

Your capabilities include:
- Helping with budgeting and expense tracking
- Providing basic tax guidance
- Assisting with financial planning and goal setting
- Offering general investment education
- Helping with debt management strategies
- Explaining financial concepts in simple terms

If the user shares expenses or financial data with you, analyze it and provide insights on:
- Major spending categories
- Potential areas to reduce expenses
- Savings opportunities
- Budget recommendations

Please be supportive, non-judgmental, and focused on helping users improve their financial wellbeing.

If asked about specific investments or complex tax situations, kindly explain that you can provide general guidance but recommend consulting with a certified financial professional for specific advice.
"""

# Initialize Flask app
app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "aiwealth-secret-key")

# In-memory storage for demo purposes
# In a production app, use a database
expense_data = {}
chat_histories = {}

# Database functions
def connect_db():
    return sqlite3.connect('database.db')

def init_db():
    conn = connect_db()
    cursor = conn.cursor()

    # Table for storing expenses (in memory for this demo)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS expenses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL,
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
            user_id TEXT NOT NULL,
            category TEXT NOT NULL,
            limit_amount REAL NOT NULL,
            spent_amount REAL DEFAULT 0,
            UNIQUE(user_id, category)
        )
    ''')

    conn.commit()
    conn.close()
    
'''
def parse_expense_message(message):
   """Extract expense details from chat messages like 'Add $45 for groceries'"""
    message = message.lower()
    if "add" in message and "$" in message and "for" in message:
        try:
            # Extract amount
            dollar_part = message.split("$")[1]
            amount_str = dollar_part.split()[0].replace(',', '')
            amount = float(amount_str)
            
            # Extract category/description
            description_part = message.split("for")[1].strip()
            
            # Map common terms to categories
            category_mapping = {
                "groceries": "food",
                "restaurant": "food",
                "dining": "food",
                "meal": "food",
                "rent": "housing",
                "mortgage": "housing",
                "utility": "housing",
                "utilities": "housing",
                "gas": "transport",
                "car": "transport",
                "bus": "transport",
                "subway": "transport",
                "movie": "entertainment",
                "game": "entertainment",
                "concert": "entertainment",
                "clothes": "shopping",
                "shoes": "shopping",
                "book": "shopping"
            }
            
            # Try to auto-categorize
            category = "other"
            for key, value in category_mapping.items():
                if key in description_part:
                    category = value
                    break
            
            return {
                "amount": amount,
                "description": description_part,
                "category": category
            }
        except:
            pass
    return None
'''

def parse_expense_message(message):
    """Extract expense details from chat messages like 'Add $45 for groceries'"""
    message = message.lower().strip()
    
    print(f"Attempting to parse expense from: '{message}'")
    
    # Simple pattern matching approach
    if ("add" in message or "spent" in message or "paid" in message) and "$" in message and ("for" in message or "on" in message):
        try:
            # Extract amount using dollar sign as reference
            parts = message.split("$")
            amount_part = parts[1].split()[0].replace(',', '')
            amount = float(amount_part)
            
            # Extract description - everything after "for" or "on"
            if "for" in message:
                description_part = message.split("for")[1].strip()
            elif "on" in message:
                description_part = message.split("on")[1].strip()
            else:
                description_part = message.split("$")[1].split(None, 1)[1].strip() if len(message.split("$")[1].split()) > 1 else "misc expense"
            
            # Category mapping - extended
            category_mapping = {
                # Food
                "groceries": "food", "grocery": "food", "restaurant": "food", 
                "dining": "food", "meal": "food", "lunch": "food", "dinner": "food",
                "breakfast": "food", "coffee": "food", "food": "food", "snack": "food",
                
                # Housing
                "rent": "housing", "mortgage": "housing", "utility": "housing", 
                "utilities": "housing", "electric": "housing", "water": "housing",
                "gas bill": "housing", "internet": "housing", "cable": "housing",
                
                # Transportation
                "gas": "transport", "fuel": "transport", "car": "transport", 
                "bus": "transport", "subway": "transport", "train": "transport",
                "taxi": "transport", "uber": "transport", "lyft": "transport",
                
                # Entertainment
                "movie": "entertainment", "game": "entertainment", "concert": "entertainment",
                "theater": "entertainment", "netflix": "entertainment", "ticket": "entertainment",
                
                # Shopping
                "clothes": "shopping", "shoes": "shopping", "book": "shopping",
                "amazon": "shopping", "gift": "shopping", "clothing": "shopping"
            }
            
            # Try to categorize
            category = "other"
            for key, value in category_mapping.items():
                if key in description_part:
                    category = value
                    break
            
            print(f"Successfully parsed expense: ${amount} for {description_part} (Category: {category})")
            
            return {
                "amount": amount,
                "description": description_part,
                "category": category
            }
        except Exception as e:
            print(f"Error parsing expense message: {str(e)}")
            return None
    
    print("Message does not match expense pattern")
    return None


@app.route('/')
def index():
    # Generate a session ID if none exists
    if 'user_id' not in session:
        session['user_id'] = f"user_{datetime.now().strftime('%Y%m%d%H%M%S')}"
    
    # Initialize chat history for this user if needed
    user_id = session['user_id']
    if user_id not in chat_histories:
        chat_histories[user_id] = []
    
    return render_template('index.html')

@app.route('/chat', methods=['POST'])
def chat():
    user_message = request.json.get('message', '')
    user_id = session.get('user_id', 'default_user')
    
    if not user_message:
        return jsonify({"response": "No message provided"})
    
    try:
        # Check if message is about adding an expense
        expense_info = parse_expense_message(user_message)
        if expense_info:
            # Add expense to the in-memory storage
            if user_id not in expense_data:
                expense_data[user_id] = []
            
            # Add expense to user's data
            expense_data[user_id].append({
                'amount': expense_info['amount'],
                'category': expense_info['category'],
                'description': expense_info['description'],
                'date': datetime.now().strftime('%Y-%m-%d')
            })
            
            # Send response about added expense
            category_name = expense_info['category'].capitalize()
            response_text = f"I've added your expense of ${expense_info['amount']:.2f} for {expense_info['description']} in the {category_name} category. You can view your spending breakdown in the dashboard."
            
            # Store response in chat history
            if user_id not in chat_histories:
                chat_histories[user_id] = []
            
            chat_histories[user_id].append({"role": "user", "parts": [user_message]})
            chat_histories[user_id].append({"role": "model", "parts": [response_text]})
            
            return jsonify({"response": response_text})
        
        # Parse budget setting commands
        if ("set budget" in user_message.lower() or "set a budget" in user_message.lower()) and "for" in user_message.lower() and "to" in user_message.lower():
            message = user_message.lower()
            # Extract category and amount
            split_for = message.split("for")[1]
            category_part = split_for.split("to")[0].strip()
            amount_part = split_for.split("to")[1].strip()
            
            # Remove dollar sign if present
            if "$" in amount_part:
                amount_part = amount_part.replace("$", "")
            
            try:
                amount = float(amount_part.replace(',', ''))
                
                # Store budget in memory (in a real app, save to database)
                # Add user to budget dictionary if not exists
                # In a real app, this would be a database update
                
                response_text = f"I've set your budget for {category_part} to ${amount:.2f}."
                
                # Store response in chat history
                if user_id not in chat_histories:
                    chat_histories[user_id] = []
                
                chat_histories[user_id].append({"role": "user", "parts": [user_message]})
                chat_histories[user_id].append({"role": "model", "parts": [response_text]})
                
                return jsonify({"response": response_text})
            except ValueError:
                pass
        
        # Regular chat processing for non-expense messages
        if user_id not in chat_histories:
            chat_histories[user_id] = []
        
        # Add the user message to chat history
        chat_histories[user_id].append({"role": "user", "parts": [user_message]})
        
        # If the Gemini API is configured
        if model:
            # If this is the first message, include the system prompt
            if len(chat_histories[user_id]) == 1:
                response = model.generate_content([SYSTEM_PROMPT, user_message])
            else:
                # Create conversation context from chat history
                convo = model.start_chat(history=chat_histories[user_id][:-1])
                response = convo.send_message(user_message)
            
            # Add the AI response to chat history
            bot_response = response.text
        else:
            # If Gemini API is not configured, use a fallback response
            bot_response = "I'm currently running in limited mode. Please configure a Gemini API key to enable all features."
        
        chat_histories[user_id].append({"role": "model", "parts": [bot_response]})
        
        return jsonify({"response": bot_response})
    
    except Exception as e:
        print(f"Error: {str(e)}")
        return jsonify({"response": f"I'm sorry, I encountered an error: {str(e)}"})
    
'''
@app.route('/dashboard')
def dashboard():
    user_id = session.get('user_id', 'default_user')
    
    # Default empty data if user hasn't added expenses
    if user_id not in expense_data or not expense_data[user_id]:
        return render_template('dashboard.html', has_data=False)
    
    # Process expense data for the dashboard
    df = pd.DataFrame(expense_data[user_id])
    
    # Create category summary
    category_summary = df.groupby('category')['amount'].sum().reset_index()
    
    # Generate the pie chart
    fig = px.pie(
        category_summary, 
        values='amount', 
        names='category', 
        title='Expense Distribution by Category',
        hole=0.4,
        color_discrete_sequence=px.colors.sequential.Viridis
    )
    fig.update_traces(textposition='inside', textinfo='percent+label')
    fig.update_layout(
        margin=dict(t=50, b=50, l=20, r=20),
        height=400,
        legend=dict(orientation="h", yanchor="bottom", y=-0.3)
    )
    
    # Convert the figure to JSON for the template
    pie_chart = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)
    
    # Get total expenses and top categories
    total_expenses = df['amount'].sum()
    top_categories = category_summary.sort_values('amount', ascending=False).head(3)
    
    # Calculate monthly average (if dates are available)
    monthly_avg = total_expenses
    if 'date' in df.columns:
        df['date'] = pd.to_datetime(df['date'])
        months = max(1, (df['date'].max() - df['date'].min()).days / 30)
        monthly_avg = total_expenses / months
    
    # Prepare data for the template
    return render_template(
        'dashboard.html',
        has_data=True,
        pie_chart=pie_chart,
        total_expenses=total_expenses,
        top_categories=top_categories.to_dict('records'),
        monthly_avg=monthly_avg,
        expenses=expense_data[user_id]
    )'''

@app.route('/dashboard')
def dashboard():
    user_id = session.get('user_id', 'default_user')
    
    # Add debug information
    print(f"Dashboard accessed by user: {user_id}")
    print(f"Available expense data: {list(expense_data.keys())}")
    
    # Default empty data if user hasn't added expenses
    if user_id not in expense_data or not expense_data[user_id]:
        print("No expense data found for user")
        return render_template('dashboard.html', has_data=False)
    
    try:
        # Process expense data for the dashboard
        df = pd.DataFrame(expense_data[user_id])
        print(f"DataFrame created with columns: {df.columns}")
        print(f"DataFrame sample: {df.head()}")
        
        # Create category summary
        category_summary = df.groupby('category')['amount'].sum().reset_index()
        
        # Prepare data for Chart.js
        categories = category_summary['category'].tolist()
        amounts = category_summary['amount'].tolist()
        
        # Get total expenses and top categories
        total_expenses = df['amount'].sum()
        top_categories = category_summary.sort_values('amount', ascending=False).head(3)
        
        # Calculate monthly average (if dates are available)
        monthly_avg = total_expenses
        if 'date' in df.columns:
            df['date'] = pd.to_datetime(df['date'])
            months = max(1, (df['date'].max() - df['date'].min()).days / 30)
            monthly_avg = total_expenses / months
        
        # Prepare data for the template
        return render_template(
            'dashboard.html',
            has_data=True,
            categories=categories,
            amounts=amounts,
            total_expenses=total_expenses,
            top_categories=top_categories.to_dict('records'),
            monthly_avg=monthly_avg,
            expenses=expense_data[user_id]
        )
    except Exception as e:
        print(f"Error in dashboard route: {str(e)}")
        import traceback
        traceback.print_exc()
        return render_template('dashboard.html', has_data=False, 
                              error=f"Error generating dashboard: {str(e)}")
    
    
@app.route('/add_expense', methods=['POST'])
def add_expense():
    user_id = session.get('user_id', 'default_user')
    
    # Ensure user has an expense list
    if user_id not in expense_data:
        expense_data[user_id] = []
    
    # Get expense details from form
    try:
        amount = float(request.form.get('amount', 0))
        category = request.form.get('category', 'Uncategorized')
        description = request.form.get('description', '')
        date = request.form.get('date', datetime.now().strftime('%Y-%m-%d'))
        
        # Add expense to user's data
        expense_data[user_id].append({
            'amount': amount,
            'category': category,
            'description': description,
            'date': date
        })
        
        return redirect('/dashboard')
    except ValueError:
        return "Invalid amount value", 400

@app.route('/delete_expense/<int:index>', methods=['POST'])
def delete_expense(index):
    user_id = session.get('user_id', 'default_user')
    
    # Delete expense if it exists
    if user_id in expense_data and 0 <= index < len(expense_data[user_id]):
        expense_data[user_id].pop(index)
    
    return redirect('/dashboard')

@app.route('/analyze_expenses', methods=['POST'])
def analyze_expenses():
    user_id = session.get('user_id', 'default_user')
    
    if user_id not in expense_data or not expense_data[user_id]:
        return jsonify({"response": "No expense data available to analyze"})
    
    try:
        # Format expenses for the AI to analyze
        df = pd.DataFrame(expense_data[user_id])
        category_summary = df.groupby('category')['amount'].sum().reset_index()
        total_expenses = df['amount'].sum()
        
        # Create a summary of expenses for analysis
        expense_summary = "Here's my expense data:\n"
        expense_summary += f"Total expenses: ${total_expenses:.2f}\n"
        expense_summary += "Breakdown by category:\n"
        
        for _, row in category_summary.iterrows():
            percentage = (row['amount'] / total_expenses) * 100
            expense_summary += f"- {row['category']}: ${row['amount']:.2f} ({percentage:.1f}%)\n"
        
        expense_summary += "\nCan you analyze my spending and provide recommendations?"
        
        # Send this data to the AI for analysis
        if model:
            response = model.generate_content([
                "You are a financial advisor analyzing expense data. Provide specific insights and recommendations.",
                expense_summary
            ])
            ai_response = response.text
        else:
            ai_response = "AI analysis is currently unavailable. Please configure a Gemini API key to enable this feature."
        
        return jsonify({"response": ai_response})
    
    except Exception as e:
        print(f"Error: {str(e)}")
        return jsonify({"response": f"I'm sorry, I encountered an error analyzing your expenses: {str(e)}"})

if __name__ == '__main__':
    init_db()
    app.run(debug=True)