import os
import re
import time
import json
import logging
from apify_client import ApifyClient
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Load environment variables
load_dotenv()

# Get API key from environment variables
apify_api_key = os.getenv('APIFY_API_KEY')

# Initialize Apify client
if not apify_api_key:
    raise ValueError("APIFY_API_KEY is not set in the .env file.")

client = ApifyClient(apify_api_key)

def validate_youtube_url(url):
    """
    Validates if the provided URL is a valid YouTube URL.
    
    Args:
        url (str): The URL to validate
        
    Returns:
        dict: A dictionary with validation result and video ID if valid
    """
    # Regular expression to match YouTube URLs and extract video ID
    youtube_regex = (
        r'(https?://)?(www\.)?'
        r'(youtube\.com/watch\?v=|youtu\.be/|youtube\.com/embed/|youtube\.com/v/|youtube\.com/e/|'
        r'youtube\.com/user/.+/|youtube\.com/channel/.+/|youtube\.com/c/.+/|'
        r'youtube\.com/playlist\?list=|youtube\.com/watch\?v=.+&list=|'
        r'youtube\.com/shorts/|youtube\.com/live/)'
        r'([a-zA-Z0-9_-]{11})'
    )
    
    match = re.search(youtube_regex, url)
    
    if match:
        video_id = match.group(4)
        return {
            "valid": True,
            "video_id": video_id,
            "url": url
        }
    else:
        return {
            "valid": False,
            "error": "Invalid YouTube URL format. Please provide a valid YouTube URL."
        }

def extract_youtube_transcript(url, retries=3, timeout=180):
    """
    Extracts transcript from a YouTube video using Apify.
    
    Args:
        url (str): The YouTube URL to extract transcript from
        retries (int): Number of retry attempts if extraction fails
        timeout (int): Maximum time to wait for extraction (in seconds)
        
    Returns:
        dict: A dictionary with extraction result and transcript if successful
    """
    # First validate the URL
    validation = validate_youtube_url(url)
    if not validation["valid"]:
        return validation
    
    logging.info(f"Extracting transcript from YouTube URL: {url}")
    
    for attempt in range(retries):
        try:
            # Prepare the Actor input
            run_input = {
                "outputFormat": "captions",
                "urls": [url],
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
            logging.info(f"Starting YouTube Actor run (attempt {attempt+1}/{retries})...")
            run = client.actor("1s7eXiaukVuOr4Ueg").call(run_input=run_input)
            
            # Check the run status
            run_info = client.run(run["id"]).get()
            
            # Wait for completion with a timeout
            start_time = time.time()
            
            while run_info['status'] in ['RUNNING', 'READY']:
                if time.time() - start_time > timeout:
                    logging.warning(f"Extraction timeout on attempt {attempt+1}. The operation took too long.")
                    break
                
                logging.info(f"Current status: {run_info['status']}. Waiting...")
                time.sleep(5)
                run_info = client.run(run["id"]).get()
            
            if run_info['status'] == 'SUCCEEDED':
                logging.info(f"Actor run completed successfully. Dataset ID: {run['defaultDatasetId']}")
                
                # Fetch results from the dataset
                items = list(client.dataset(run["defaultDatasetId"]).iterate_items())
                
                if not items:
                    logging.warning("No transcript data found. The video might not have captions available.")
                    continue
                
                # Extract transcript data from items
                video_data = items[0]  # Assuming we're only processing one video
                
                # Check if captions exist
                if 'captions' not in video_data or not video_data['captions']:
                    logging.warning("No captions found in the video data.")
                    continue
                
                # Process the transcript into a cleaner format
                transcript_text = ""
                captions = []
                
                for caption in video_data['captions']:
                    if 'text' in caption:
                        transcript_text += caption['text'] + " "
                        
                        # Store caption with timestamp if available
                        caption_entry = {
                            "text": caption['text']
                        }
                        
                        if 'start' in caption:
                            caption_entry["start"] = caption['start']
                        if 'duration' in caption:
                            caption_entry["duration"] = caption['duration']
                            
                        captions.append(caption_entry)
                
                # Basic video info
                video_info = {
                    "title": video_data.get('title', 'Unknown Title'),
                    "channel": video_data.get('channelName', 'Unknown Channel'),
                    "published_date": video_data.get('datePublished', 'Unknown Date'),
                    "video_id": validation["video_id"],
                    "url": url
                }
                
                return {
                    "success": True,
                    "video_info": video_info,
                    "transcript": transcript_text.strip(),
                    "captions": captions,
                    "raw_data": video_data
                }
            else:
                error_message = run_info.get('errorMessage', 'Unknown error occurred')
                logging.warning(f"Actor run failed on attempt {attempt+1}: {error_message}")
        
        except Exception as e:
            logging.error(f"Error during transcript extraction (attempt {attempt+1}): {str(e)}")
        
        # Wait before retrying
        if attempt < retries - 1:
            wait_time = (attempt + 1) * 5  # Exponential backoff
            logging.info(f"Waiting {wait_time} seconds before retrying...")
            time.sleep(wait_time)
    
    # All attempts failed
    return {
        "success": False,
        "error": f"Failed to extract transcript after {retries} attempts."
    }

def save_transcript_to_file(transcript_data, output_file="transcript.json"):
    """
    Saves the transcript data to a JSON file.
    
    Args:
        transcript_data (dict): The transcript data to save
        output_file (str): The filename to save the transcript to
        
    Returns:
        dict: A dictionary with saving result and file path if successful
    """
    if not transcript_data:
        return {
            "success": False,
            "error": "No transcript data provided to save."
        }
    
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(transcript_data, f, indent=2, ensure_ascii=False)
        
        return {
            "success": True,
            "file_path": os.path.abspath(output_file),
            "message": f"Successfully saved transcript to {output_file}"
        }
    
    except Exception as e:
        logging.error(f"Error saving transcript file: {str(e)}")
        return {
            "success": False,
            "error": f"Failed to save transcript file: {str(e)}"
        }

# Unit tests
def test_validate_youtube_url():
    """Test the YouTube URL validation function."""
    # Valid YouTube URLs
    valid_urls = [
        "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
        "https://youtu.be/dQw4w9WgXcQ",
        "https://www.youtube.com/embed/dQw4w9WgXcQ",
        "https://www.youtube.com/shorts/dQw4w9WgXcQ",
        "http://youtu.be/dQw4w9WgXcQ"
    ]
    
    # Invalid YouTube URLs
    invalid_urls = [
        "https://www.youtube.com/",
        "https://www.google.com/",
        "https://youtu.be/",
        "https://www.youtube.com/watch?v=",
        "random_text"
    ]
    
    print("Testing YouTube URL validation...")
    
    # Test valid URLs
    for url in valid_urls:
        result = validate_youtube_url(url)
        assert result["valid"] == True, f"Failed to validate valid URL: {url}"
        assert "video_id" in result, f"Missing video_id in result for URL: {url}"
        print(f"✓ Valid URL test passed: {url}")
    
    # Test invalid URLs
    for url in invalid_urls:
        result = validate_youtube_url(url)
        assert result["valid"] == False, f"Incorrectly validated invalid URL: {url}"
        assert "error" in result, f"Missing error message in result for URL: {url}"
        print(f"✓ Invalid URL test passed: {url}")
    
    print("All YouTube URL validation tests passed!")

if __name__ == "__main__":
    # Run tests when module is executed directly
    test_validate_youtube_url()