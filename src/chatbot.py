def get_chatbot_response(user_input):
    """Returns chatbot responses based on user queries."""
    responses = {
        "hello": "Hello! How can I assist you with your expenses today?",
        "help": "You can ask me about spending, transaction summaries, or budget checks.",
        "spending": "I can show you your recent spending by category.",
        "budget": "You can check if you've exceeded your budget by category."
    }

    user_input = user_input.lower()
    for keyword, response in responses.items():
        if keyword in user_input:
            return response

    return "I'm sorry, I didn't quite understand that. Can you ask something else?"
