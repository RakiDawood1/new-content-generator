import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

def get_api_key(service_name):
    """Retrieve API key for the specified service."""
    return os.getenv(service_name)

def handle_api_error(error):
    """Log and handle API errors."""
    print(f"API Error: {error}")
    # Additional error handling logic can be added here
