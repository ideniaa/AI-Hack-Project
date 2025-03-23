import os
import json
import pandas as pd
import plotly
import plotly.express as px
from flask import Flask, render_template, request, jsonify, session, redirect, url_for
import google.generativeai as genai
from dotenv import load_dotenv
from datetime import datetime

# Load environment variables
load_dotenv()

# Configure Gemini API
# In your app.py, update the Gemini API configuration section:

# Configure Gemini API (will use this for complex financial analysis)
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
        # Get or initialize chat history
        if user_id not in chat_histories:
            chat_histories[user_id] = []
        
        # Add the user message to chat history
        chat_histories[user_id].append({"role": "user", "parts": [user_message]})
        
        # If this is the first message, include the system prompt
        if len(chat_histories[user_id]) == 1:
            response = model.generate_content([SYSTEM_PROMPT, user_message])
        else:
            # Create conversation context from chat history
            convo = model.start_chat(history=chat_histories[user_id][:-1])
            response = convo.send_message(user_message)
        
        # Add the AI response to chat history
        bot_response = response.text
        chat_histories[user_id].append({"role": "model", "parts": [bot_response]})
        
        return jsonify({"response": bot_response})
    
    except Exception as e:
        print(f"Error: {str(e)}")
        return jsonify({"response": f"I'm sorry, I encountered an error: {str(e)}"})

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
        months = (df['date'].max() - df['date'].min()).days / 30
        if months >= 1:
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
    )

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
        response = model.generate_content([
            "You are a financial advisor analyzing expense data. Provide specific insights and recommendations.",
            expense_summary
        ])
        
        return jsonify({"response": response.text})
    
    except Exception as e:
        print(f"Error: {str(e)}")
        return jsonify({"response": f"I'm sorry, I encountered an error analyzing your expenses: {str(e)}"})

if __name__ == '__main__':
    app.run(debug=True)


@app.route('/test')
def test():
    return "<h1>Test Route Working</h1>"