import os
from dotenv import load_dotenv

# Load environment variables from .env file if it exists
# This allows easy configuration for local development
dotenv_path = os.path.join(os.path.dirname(__file__), '.env')
if os.path.exists(dotenv_path):
    load_dotenv(dotenv_path)

# Import the Flask app
from app import app  # noqa: E402

if __name__ == '__main__':
    # Get port from environment variable or default to 5000
    port = int(os.environ.get('PORT', 5000))
    # Run the app, binding to 0.0.0.0 so it's accessible externally
    app.run(host='0.0.0.0', port=port, debug=True)