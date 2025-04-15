from apify_client import ApifyClient
from utils.helpers import handle_api_error
import google.generativeai as genai
import os
import time
from dotenv import load_dotenv
import logging  # Import logging module

# Load environment variables from .env file
load_dotenv()

# Get API key from environment variables
apify_api_key = os.getenv('APIFY_API_KEY')
gemini_api_key = os.getenv('GEMINI_API_KEY')

# Check if API key is loaded
if not apify_api_key:
    raise ValueError("APIFY_API_KEY is not set in the .env file.")
if not gemini_api_key:
    raise ValueError("GEMINI_API_KEY is not set in the .env file.")

# Initialize Apify client with the API token from the .env file
client = ApifyClient(apify_api_key)

# Configure Gemini API
genai.configure(api_key=gemini_api_key)

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def test_apify_account():
    """Test basic Apify API connectivity by retrieving account information"""
    logging.info("--- Testing Apify Account Access ---")
    try:
        # Get account information to verify the API key works
        account_info = client.user().get()
        logging.info(f"Successfully connected to Apify account: {account_info['username']}")
        logging.info(f"Account plan: {account_info.get('plan', 'Unknown')}")
        logging.info(f"Account createdAt: {account_info.get('createdAt', 'Unknown')}")
        return True
    except Exception as e:
        logging.error(f"Failed to connect to Apify account: {str(e)}")
        handle_api_error(e)
        return False

def test_apify_youtube_actor(youtube_url):
    """Test the YouTube transcript extraction Actor with a specific YouTube URL"""
    logging.info(f"\nTesting YouTube transcript extraction with URL: {youtube_url}")
    
    try:
        # Prepare the Actor input
        run_input = {
            "outputFormat": "captions",
            "urls": [youtube_url],
            "maxRetries": 8,
            "channelHandleBoolean": True,
            "channelNameBoolean": True,
            "channelIDBoolean": False,
            "subscriberCountBoolean": False,
            "dateTextBoolean": False,
            "relativeDateTextBoolean": True,
            "datePublishedBoolean": True,
            "uploadDateBoolean": False,
            "viewCountBoolean": False,
            "likesBoolean": False,
            "commentsBoolean": False,
            "keywordsBoolean": False,
            "thumbnailBoolean": False,
            "descriptionBoolean": False,
            "proxyOptions": {
                "useApifyProxy": True,
                "apifyProxyGroups": [
                    "RESIDENTIAL"
                ],
                "apifyProxyCountry": "LK"
            },
        }

        # Run the YouTube transcript Actor and wait for it to finish
        logging.info("Starting YouTube Actor run...")
        run = client.actor("1s7eXiaukVuOr4Ueg").call(run_input=run_input)
        
        # Check the run status
        run_info = client.run(run["id"]).get()
        logging.info(f"Run status: {run_info['status']}")
        
        if run_info['status'] in ['RUNNING', 'READY']:
            logging.info("Actor is still processing. Waiting for completion...")
            # Wait for up to 60 seconds for the run to complete
            for _ in range(12):  # 12 * 5 = 60 seconds
                time.sleep(5)
                run_info = client.run(run["id"]).get()
                logging.info(f"Current status: {run_info['status']}")
                if run_info['status'] not in ['RUNNING', 'READY']:
                    break
        
        if run_info['status'] == 'SUCCEEDED':
            logging.info(f"Actor run completed successfully. Dataset ID: {run['defaultDatasetId']}")
            # Fetch and print Actor results from the run's dataset
            results_found = False
            for item in client.dataset(run["defaultDatasetId"]).iterate_items():
                results_found = True
                logging.info("YouTube transcript data retrieved successfully:")
                logging.info(item)
                # Just print the first item to avoid overwhelming output
                break
                
            if not results_found:
                logging.info("No data found in the dataset. The Actor ran successfully but didn't produce results.")
                logging.info("This might happen if the video doesn't have captions or they're not accessible.")
            
            return True
        else:
            logging.info(f"Actor run did not complete successfully. Final status: {run_info['status']}")
            if 'errorMessage' in run_info:
                logging.error(f"Error message: {run_info['errorMessage']}")
            return False
            
    except Exception as e:
        logging.error(f"YouTube transcript extraction test failed: {str(e)}")
        handle_api_error(e)
        return False

def test_apify_hello_world():
    """Test a simple Hello World actor to verify basic Apify functionality"""
    logging.info("\n--- Testing Apify Hello World Actor ---")
    try:
        # Run a simple Hello World actor
        logging.info("Starting Hello World Actor run...")
        run = client.actor("apify/hello-world").call()
        
        # Check the run status
        run_info = client.run(run["id"]).get()
        logging.info(f"Run status: {run_info['status']}")
        
        if run_info['status'] == 'SUCCEEDED':
            logging.info("Hello World Actor run completed successfully.")
            
            # Fetch and print Actor results
            log_content = client.log(run["id"]).get(format="text")
            logging.info("\nLog output:")
            logging.info(log_content[:500] + "..." if len(log_content) > 500 else log_content)
            
            # Get dataset items if any
            dataset_items = list(client.dataset(run["defaultDatasetId"]).iterate_items())
            if dataset_items:
                logging.info("\nDataset items:")
                for item in dataset_items[:3]:  # Show at most 3 items
                    logging.info(item)
            
            logging.info("\nHello World Actor test completed successfully.")
            return True
        else:
            logging.info(f"Hello World Actor run did not complete successfully. Final status: {run_info['status']}")
            if 'errorMessage' in run_info:
                logging.error(f"Error message: {run_info['errorMessage']}")
            return False
    
    except Exception as e:
        logging.error(f"Hello World Actor test failed: {str(e)}")
        handle_api_error(e)
        return False

def test_gemini_integration():
    """Test the Gemini integration"""
    logging.info("\n--- Testing Gemini Integration ---")
    try:
        gemini_model = genai.GenerativeModel(model_name="gemini-1.5-pro")
        response = gemini_model.generate_content("Hello, how can I assist you today?")
        logging.info("Gemini client is working. Response:")
        logging.info(response.text)
        logging.info("Gemini integration test completed successfully.")
        return True
    except Exception as e:
        logging.error(f"Gemini integration test failed: {str(e)}")
        handle_api_error(e)
        return False

def test_api_integrations():
    logging.info("Starting API integration tests...")
    
    # Test Apify account access
    account_success = test_apify_account()
    
    # Test simple Hello World actor first
    hello_world_success = test_apify_hello_world() if account_success else False
    
    # Test URLs - try popular videos with captions
    test_urls = [
        "https://www.youtube.com/watch?v=dQw4w9WgXcQ",  # Rick Astley - Never Gonna Give You Up (likely has captions)
        "https://www.youtube.com/watch?v=jNQXAC9IVRw",  # "Me at the zoo" - First YouTube video
        "https://www.youtube.com/watch?v=b_nep8vMnkc"   # Original test URL
    ]
    
    # Test YouTube transcript actor with multiple URLs if needed
    youtube_success = False
    if account_success:
        logging.info("\n--- Testing Apify YouTube Transcript Actor ---")
        for url in test_urls:
            youtube_success = test_apify_youtube_actor(url)
            if youtube_success:
                break
    
    # Test Gemini client
    gemini_success = test_gemini_integration()
    
    # Summary
    logging.info("\n--- API Integration Test Summary ---")
    logging.info(f"Apify Account Access: {'SUCCESS' if account_success else 'FAILED'}")
    logging.info(f"Apify Hello World Actor: {'SUCCESS' if hello_world_success else 'FAILED'}")
    logging.info(f"Apify YouTube Transcript Actor: {'SUCCESS' if youtube_success else 'NOT TESTED' if not account_success else 'FAILED'}")
    logging.info(f"Gemini integration: {'SUCCESS' if gemini_success else 'FAILED'}")
    
    if account_success and hello_world_success:
        logging.info("Apify integration is working correctly at a basic level.")
        if not youtube_success:
            logging.warning("However, the YouTube transcript actor is not returning results.")
            logging.warning("This might be due to specific limitations with the actor or the videos being tested.")
            logging.warning("You may want to try a different actor or adjust the configuration.")
    elif not account_success:
        logging.error("Apify account access failed. Please check your API key.")
    elif not hello_world_success:
        logging.error("Apify Hello World actor test failed. There might be an issue with the Apify platform or your account permissions.")

# Commenting out the test function call for production
# test_api_integrations()
