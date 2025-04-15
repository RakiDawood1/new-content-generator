import logging
import time
from agents.agent_setup import RepurposerAgentSystem
from dotenv import load_dotenv
from apify_client import ApifyClient
import os

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# Test URLs - multiple options in case some fail
TEST_URLS = [
    "https://www.youtube.com/watch?v=dQw4w9WgXcQ",  # Rick Astley - Never Gonna Give You Up
    "https://www.youtube.com/watch?v=jNQXAC9IVRw",  # "Me at the zoo" - First YouTube video
    "https://www.youtube.com/watch?v=9bZkp7q19f0",  # PSY - GANGNAM STYLE - known to have captions
]

def check_apify_limits():
    """Check current Apify account usage and limits."""
    try:
        client = ApifyClient(os.getenv('APIFY_API_KEY'))
        account_info = client.user().get()
        
        # Log account information
        logging.info("Apify Account Status:")
        logging.info(f"- Username: {account_info.get('username', 'Unknown')}")
        logging.info(f"- Plan: {account_info.get('plan', {}).get('id', 'Unknown')}")
        
        # Get compute units info if available
        plan = account_info.get('plan', {})
        max_units = plan.get('maxMonthlyActorComputeUnits', 'Unknown')
        logging.info(f"- Max Monthly Compute Units: {max_units}")
        
        # Get proxy limits if available
        max_proxy = plan.get('maxMonthlyResidentialProxyGbytes', 'Unknown')
        logging.info(f"- Max Monthly Proxy GB: {max_proxy}")
        
        # Get retention info
        retention = plan.get('dataRetentionDays', 'Unknown')
        logging.info(f"- Data Retention Days: {retention}")
        
        return True
    
    except Exception as e:
        logging.error(f"Failed to check Apify limits: {str(e)}")
        return False

def test_full_workflow(url):
    """
    Test the complete content repurposing workflow with a given YouTube video.
    
    Args:
        url (str): YouTube URL to test with
        
    Returns:
        dict: Test results including success status and any output
    """
    start_time = time.time()  # Move this to the beginning
    
    try:
        logging.info(f"\nTesting workflow with URL: {url}")
        
        # Create the RepurposerAgentSystem
        system = RepurposerAgentSystem()
        
        # Process the URL through the complete pipeline
        result = system.process_youtube_url(url)
        processing_time = time.time() - start_time
        
        if result["success"]:
            content_data = result["content_data"]
            
            # Compile test results
            test_results = {
                "success": True,
                "url": url,
                "processing_time": processing_time,
                "output_file": result["output_file"],
                "stats": {
                    "blog_posts": len(content_data["blog_posts"]),
                    "linkedin_posts": len(content_data["linkedin_posts"]),
                    "twitter_posts": len(content_data["twitter_posts"])
                }
            }
            
            # Log success details
            logging.info("✓ Workflow completed successfully!")
            logging.info(f"Processing time: {processing_time:.2f} seconds")
            logging.info(f"Output file: {result['output_file']}")
            logging.info("\nContent Generation Stats:")
            logging.info(f"- Blog Posts: {test_results['stats']['blog_posts']}")
            logging.info(f"- LinkedIn Posts: {test_results['stats']['linkedin_posts']}")
            logging.info(f"- Twitter Posts: {test_results['stats']['twitter_posts']}")
            
            return test_results
        else:
            logging.error(f"Workflow failed: {result.get('error', 'Unknown error')}")
            return {
                "success": False,
                "url": url,
                "error": result.get('error', 'Unknown error'),
                "processing_time": processing_time
            }
    
    except Exception as e:
        processing_time = time.time() - start_time
        logging.error(f"Test failed with error: {str(e)}")
        return {
            "success": False,
            "url": url,
            "error": str(e),
            "processing_time": processing_time
        }

def main():
    """
    Main function to run all tests.
    """
    load_dotenv()
    
    logging.info("Starting Enhanced Content Repurposer Tool tests...")
    
    # Check Apify account limits first
    if not check_apify_limits():
        logging.error("Failed to verify Apify account status. Proceeding with caution...")
    
    # Try each test URL until one succeeds
    test_results = []
    success = False
    
    for url in TEST_URLS:
        result = test_full_workflow(url)
        test_results.append(result)
        
        if result["success"]:
            success = True
            break
        else:
            logging.warning(f"Test failed for URL: {url}")
            logging.warning("Trying next URL...\n")
    
    # Print final summary
    logging.info("\n=== Test Summary ===")
    logging.info(f"Overall Status: {'PASSED' if success else 'FAILED'}")
    logging.info(f"URLs Attempted: {len(test_results)}")
    
    for i, result in enumerate(test_results, 1):
        logging.info(f"\nTest {i}:")
        logging.info(f"URL: {result['url']}")
        logging.info(f"Status: {'Success' if result['success'] else 'Failed'}")
        logging.info(f"Processing Time: {result.get('processing_time', 'N/A'):.2f} seconds")
        
        if result['success']:
            logging.info("Content Generated:")
            logging.info(f"- Blog Posts: {result['stats']['blog_posts']}")
            logging.info(f"- LinkedIn Posts: {result['stats']['linkedin_posts']}")
            logging.info(f"- Twitter Posts: {result['stats']['twitter_posts']}")
        else:
            logging.info(f"Error: {result.get('error', 'Unknown error')}")

if __name__ == "__main__":
    main()