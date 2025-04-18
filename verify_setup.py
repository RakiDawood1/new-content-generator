import os
import logging
from dotenv import load_dotenv
from apify_client import ApifyClient
from openai import OpenAI

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Load environment variables
load_dotenv()

# Required API keys and their descriptions
required_keys = {
    'APIFY_API_KEY': 'Apify',
    'DEEPSEEK_API_KEY': 'DeepSeek'
}

def verify_env():
    """
    Verify that all required environment variables are set.
    """
    missing_keys = []
    for key in required_keys:
        if not os.getenv(key):
            missing_keys.append(key)
    
    if missing_keys:
        logging.error("Missing required environment variables:")
        for key in missing_keys:
            logging.error(f"- {key} ({required_keys[key]})")
        return False
    
    logging.info("✓ All required environment variables are set")
    return True

def verify_apify():
    """
    Verify Apify API connection and access.
    """
    try:
        client = ApifyClient(os.getenv('APIFY_API_KEY'))
        me = client.user().get()
        logging.info("✓ Successfully connected to Apify API")
        return True
    except Exception as e:
        logging.error(f"Failed to connect to Apify API: {str(e)}")
        return False

def verify_deepseek():
    """
    Verify DeepSeek API connection and access.
    """
    try:
        client = OpenAI(
            api_key=os.getenv('DEEPSEEK_API_KEY'),
            base_url="https://api.deepseek.com/v1"
        )
        
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=[{"role": "user", "content": "Say hello"}],
            temperature=0.7,
            max_tokens=10
        )
        
        if response.choices[0].message.content:
            logging.info("✓ Successfully connected to DeepSeek API")
            return True
        else:
            logging.error("Failed to get valid response from DeepSeek API")
            return False
            
    except Exception as e:
        logging.error(f"Failed to connect to DeepSeek API: {str(e)}")
        return False

def main():
    """
    Run all verifications and report status.
    """
    logging.info("Verifying setup...")
    
    env_ok = verify_env()
    apify_ok = verify_apify()
    deepseek_ok = verify_deepseek()
    
    logging.info("\nVerification Results:")
    logging.info(f"Environment Variables: {'✓' if env_ok else '✗'}")
    logging.info(f"Apify API: {'✓' if apify_ok else '✗'}")
    logging.info(f"DeepSeek API: {'✓' if deepseek_ok else '✗'}")
    
    all_ok = env_ok and apify_ok and deepseek_ok
    
    if all_ok:
        logging.info("\n✓ All systems verified and ready")
    else:
        logging.error("\n✗ Some verifications failed. Please check the logs above.")
    
    return all_ok

if __name__ == "__main__":
    main()