import os
import logging
from dotenv import load_dotenv
from apify_client import ApifyClient
import google.generativeai as genai

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def verify_environment():
    """
    Verify that all required environment variables are set.
    """
    load_dotenv()
    
    required_vars = {
        'APIFY_API_KEY': 'Apify',
        'GEMINI_API_KEY': 'Google Gemini'
    }
    
    missing_vars = []
    for var, service in required_vars.items():
        if not os.getenv(var):
            missing_vars.append(f"{var} ({service})")
    
    if missing_vars:
        logging.error("Missing required environment variables:")
        for var in missing_vars:
            logging.error(f"- {var}")
        return False
    
    logging.info("✓ All required environment variables are set")
    return True

def verify_apify():
    """
    Verify Apify API connection and access.
    """
    try:
        client = ApifyClient(os.getenv('APIFY_API_KEY'))
        user_info = client.user().get()
        
        logging.info("✓ Successfully connected to Apify")
        logging.info(f"  Username: {user_info['username']}")
        logging.info(f"  Plan: {user_info.get('plan', 'Unknown')}")
        return True
    
    except Exception as e:
        logging.error(f"Failed to connect to Apify: {str(e)}")
        return False

def verify_gemini():
    """
    Verify Google Gemini API connection and access.
    """
    try:
        genai.configure(api_key=os.getenv('GEMINI_API_KEY'))
        model = genai.GenerativeModel('gemini-1.5-pro')
        
        # Test with a simple prompt
        response = model.generate_content("Hello, are you working?")
        
        if response and hasattr(response, 'text'):
            logging.info("✓ Successfully connected to Google Gemini API")
            return True
        else:
            logging.error("Failed to get valid response from Gemini API")
            return False
    
    except Exception as e:
        logging.error(f"Failed to connect to Gemini API: {str(e)}")
        return False

def main():
    """
    Run all verification checks.
    """
    logging.info("Starting setup verification...")
    
    # Check environment variables
    env_ok = verify_environment()
    
    # Only proceed with API checks if environment is set up
    if env_ok:
        apify_ok = verify_apify()
        gemini_ok = verify_gemini()
        
        # Print final results
        logging.info("\n=== Verification Results ===")
        logging.info(f"Environment Variables: {'✓' if env_ok else '✗'}")
        logging.info(f"Apify API: {'✓' if apify_ok else '✗'}")
        logging.info(f"Gemini API: {'✓' if gemini_ok else '✗'}")
        
        all_ok = env_ok and apify_ok and gemini_ok
        logging.info(f"\nOverall Status: {'READY' if all_ok else 'NOT READY'}")
        
        return all_ok
    else:
        logging.error("\nSetup verification failed: Missing environment variables")
        return False

if __name__ == "__main__":
    main()