import requests
import json
import time

# Base URL for the Flask application
BASE_URL = "http://localhost:5000"

def test_chatbot():
    """Test basic chatbot functionality"""
    print("\n=== Testing Chatbot ===")
    
    # Test greeting
    response = requests.post(f"{BASE_URL}/chat", 
                             json={"message": "Hello there!"})
    print(f"Greeting response: {response.json()['response']}")
    
    # Test help
    response = requests.post(f"{BASE_URL}/chat", 
                             json={"message": "What can you do?"})
    print(f"Help response: {response.json()['response']}")
    
    return True

def test_budget_management():
    """Test budget setting and retrieval"""
    print("\n=== Testing Budget Management ===")
    
    # Set a budget for food
    response = requests.post(f"{BASE_URL}/set_budget", 
                             json={"category": "food", "limit_amount": 400})
    print(f"Set budget response: {response.json()['message']}")
    
    # Get budget info via direct endpoint
    response = requests.get(f"{BASE_URL}/get_budget?category=food")
    budget_info = response.json()
    print(f"Get budget response: {json.dumps(budget_info, indent=2)}")
    
    # Get budget info via chat
    response = requests.post(f"{BASE_URL}/chat", 
                             json={"message": "What's my budget for food?"})
    print(f"Budget via chat: {response.json()['response']}")
    
    return True

def test_expense_tracking():
    """Test expense addition and categorization"""
    print("\n=== Testing Expense Tracking ===")
    
    # Add expense via direct endpoint
    response = requests.post(f"{BASE_URL}/add_expense", 
                             json={"amount": 35.75, "description": "Italian restaurant"})
    print(f"Add expense response: {response.json()['message']}")
    
    # Add expense via natural language
    response = requests.post(f"{BASE_URL}/chat", 
                             json={"message": "Add $25.99 for movie tickets"})
    print(f"Natural language expense: {response.json()['response']}")
    
    # Check budget to see if expenses were added
    response = requests.get(f"{BASE_URL}/get_budget?category=food")
    print(f"Food budget after restaurant expense: {json.dumps(response.json(), indent=2)}")
    
    response = requests.get(f"{BASE_URL}/get_budget?category=entertainment")
    print(f"Entertainment budget after movie expense: {json.dumps(response.json(), indent=2)}")
    
    return True

def test_budget_advice():
    """Test budget advice when approaching limit"""
    print("\n=== Testing Budget Advice ===")
    
    # Set a small budget
    response = requests.post(f"{BASE_URL}/set_budget", 
                             json={"category": "shopping", "limit_amount": 50})
    
    # Add expense that's close to the limit
    response = requests.post(f"{BASE_URL}/add_expense", 
                             json={"amount": 45, "description": "new shoes"})
    
    # Check budget advice
    response = requests.get(f"{BASE_URL}/get_budget?category=shopping")
    advice = response.json()["advice"]
    print(f"Budget advice when near limit: {advice}")
    
    return True

def run_all_tests():
    """Run all test functions"""
    print("Starting tests for Financial Advisor Bot...")
    
    tests = [
        test_chatbot,
        test_budget_management,
        test_expense_tracking,
        test_budget_advice
    ]
    
    results = []
    for test in tests:
        try:
            result = test()
            results.append((test.__name__, result))
        except Exception as e:
            print(f"Error in {test.__name__}: {str(e)}")
            results.append((test.__name__, False))
    
    # Print summary
    print("\n=== Test Results ===")
    for name, result in results:
        status = "PASSED" if result else "FAILED"
        print(f"{name}: {status}")

if __name__ == "__main__":
    # Wait a moment to ensure Flask app is running
    print("Make sure your Flask application is running before continuing...")
    time.sleep(1)
    run_all_tests()