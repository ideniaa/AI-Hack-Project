# We will build the back-end here (app.py will be the main file for the back-end)

# Load environment variables
load_dotenv()

# Configure Gemini API
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

# Set up the model - we will use the Gemini 2.0 Flash-Lite model
# This is a smaller model that is optimized for speed and can be used for real-time applications
model = genai.GenerativeModel('Gemini 2.0 Flash-Lite')

