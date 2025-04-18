import os
import logging
from dotenv import load_dotenv
from agents.agent_setup import RepurposerAgentSystem

# Load environment variables from .env file
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def run_content_repurposer():
    """Main function to run the content repurposing pipeline."""
    logging.info("--- Starting Content Repurposer Tool ---")
    
    # Get YouTube URL from user
    youtube_url = input("Please enter the YouTube URL you want to process: ")
    
    if not youtube_url:
        logging.error("No YouTube URL provided. Exiting.")
        return

    logging.info(f"Processing URL: {youtube_url}")

    try:
        # Initialize the agent system
        agent_system = RepurposerAgentSystem()
        
        # Process the URL
        result = agent_system.process_youtube_url(youtube_url)
        
        # Output the results
        if result.get("success"):
            logging.info("--- Content Repurposing Complete ---")
            logging.info(f"Final output saved to: {result.get('output_path', 'N/A')}")
        else:
            logging.error("--- Content Repurposing Failed ---")
            logging.error(f"Error: {result.get('error', 'Unknown error')}")
            
    except Exception as e:
        logging.exception(f"An unexpected error occurred during the repurposing process: {str(e)}")

if __name__ == "__main__":
    run_content_repurposer()
