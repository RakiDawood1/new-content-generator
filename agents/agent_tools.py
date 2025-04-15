import os
import json
import re
import time
import logging
from apify_client import ApifyClient
import google.generativeai as genai
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Load environment variables
load_dotenv()

# Initialize Apify client
apify_api_key = os.getenv('APIFY_API_KEY')
gemini_api_key = os.getenv('GEMINI_API_KEY')

if not apify_api_key:
    raise ValueError("APIFY_API_KEY is not set in the .env file.")
if not gemini_api_key:
    raise ValueError("GEMINI_API_KEY is not set in the .env file.")

client = ApifyClient(apify_api_key)
genai.configure(api_key=gemini_api_key)

# Tool functions for agents

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

def extract_youtube_transcript(url):
    """
    Extracts transcript from a YouTube video using Apify.
    
    Args:
        url (str): The YouTube URL to extract transcript from
        
    Returns:
        dict: A dictionary with extraction result and transcript if successful
    """
    # First validate the URL
    validation = validate_youtube_url(url)
    if not validation["valid"]:
        return validation
    
    logging.info(f"Extracting transcript from YouTube URL: {url}")
    
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
        logging.info("Starting YouTube Actor run...")
        run = client.actor("1s7eXiaukVuOr4Ueg").call(run_input=run_input)
        
        # Check the run status
        run_info = client.run(run["id"]).get()
        
        # Wait for completion with a timeout
        max_wait_time = 180  # 3 minutes timeout
        start_time = time.time()
        
        while run_info['status'] in ['RUNNING', 'READY']:
            if time.time() - start_time > max_wait_time:
                return {
                    "success": False,
                    "error": "Extraction timeout. The operation took too long to complete."
                }
            
            logging.info(f"Current status: {run_info['status']}. Waiting...")
            time.sleep(5)
            run_info = client.run(run["id"]).get()
        
        if run_info['status'] == 'SUCCEEDED':
            logging.info(f"Actor run completed successfully. Dataset ID: {run['defaultDatasetId']}")
            
            # Fetch results from the dataset
            items = list(client.dataset(run["defaultDatasetId"]).iterate_items())
            
            if not items:
                return {
                    "success": False,
                    "error": "No transcript data found. The video might not have captions available."
                }
            
            # Extract transcript data from items
            video_data = items[0]  # Assuming we're only processing one video
            
            # Check if captions exist
            if 'captions' not in video_data or not video_data['captions']:
                return {
                    "success": False,
                    "error": "No captions found in the video data."
                }
            
            # Process the transcript into a cleaner format
            transcript_text = ""
            for caption in video_data['captions']:
                if 'text' in caption:
                    transcript_text += caption['text'] + " "
            
            # Basic video info
            video_info = {
                "title": video_data.get('title', 'Unknown Title'),
                "channel": video_data.get('channelName', 'Unknown Channel'),
                "published_date": video_data.get('datePublished', 'Unknown Date')
            }
            
            return {
                "success": True,
                "video_info": video_info,
                "transcript": transcript_text.strip(),
                "raw_data": video_data
            }
        else:
            error_message = run_info.get('errorMessage', 'Unknown error occurred')
            return {
                "success": False,
                "error": f"Actor run failed: {error_message}"
            }
    
    except Exception as e:
        logging.error(f"Error during transcript extraction: {str(e)}")
        return {
            "success": False,
            "error": f"Extraction error: {str(e)}"
        }

def refine_transcript(transcript_text):
    """
    Refines a transcript using Gemini to fix errors and improve quality.
    
    Args:
        transcript_text (str): The raw transcript text to refine
        
    Returns:
        dict: A dictionary with refinement result and refined transcript if successful
    """
    if not transcript_text or transcript_text.strip() == "":
        return {
            "success": False,
            "error": "Empty transcript provided. Nothing to refine."
        }
    
    logging.info("Refining transcript with Gemini...")
    
    try:
        # Use Gemini to refine the transcript
        gemini_model = genai.GenerativeModel(model_name="gemini-1.5-pro")
        
        prompt = f"""
        Please refine the following transcript for clarity, grammar, and accuracy. Fix any transcription errors 
        based on context, correct misspellings, and improve the overall readability while maintaining the 
        original meaning and content.
        
        Transcript:
        {transcript_text}
        """
        
        response = gemini_model.generate_content(prompt)
        
        if response and hasattr(response, 'text'):
            refined_transcript = response.text.strip()
            return {
                "success": True,
                "original_transcript": transcript_text,
                "refined_transcript": refined_transcript
            }
        else:
            return {
                "success": False,
                "error": "Failed to generate refined transcript. Empty or invalid response from Gemini."
            }
    
    except Exception as e:
        logging.error(f"Error during transcript refinement: {str(e)}")
        return {
            "success": False,
            "error": f"Refinement error: {str(e)}"
        }

def generate_content_topics(refined_transcript):
    """
    Generates content topics for different platforms based on the refined transcript.
    
    Args:
        refined_transcript (str): The refined transcript text
        
    Returns:
        dict: A dictionary with topic generation result and topics if successful
    """
    if not refined_transcript or refined_transcript.strip() == "":
        return {
            "success": False,
            "error": "Empty transcript provided. Cannot generate topics."
        }
    
    logging.info("Generating content topics with Gemini...")
    
    try:
        # Use Gemini to generate topics
        gemini_model = genai.GenerativeModel(model_name="gemini-1.5-pro", temperature=0.8)
        
        prompt = f"""
        Based on the following transcript, generate 15 unique content topics:
        - 5 blog post topics (posts up to 500 words)
        - 5 LinkedIn post topics (posts up to 100 words)
        - 5 Twitter post topics (posts up to 280 characters)
        
        Ensure each topic is appropriate for its platform, audience, and length constraints.
        For each topic, provide a brief description of what the content should cover.
        
        Format your response as JSON with three arrays: "blog_topics", "linkedin_topics", and "twitter_topics".
        
        Transcript:
        {refined_transcript}
        """
        
        response = gemini_model.generate_content(prompt)
        
        if response and hasattr(response, 'text'):
            # Try to parse JSON from the response
            try:
                # Extract JSON from response if it's embedded in text
                response_text = response.text
                
                # Find JSON content if wrapped in backticks or other formatting
                json_match = re.search(r'```json\s*([\s\S]*?)\s*```', response_text)
                if json_match:
                    json_str = json_match.group(1)
                else:
                    # Try to find JSON-like content between curly braces
                    json_match = re.search(r'(\{[\s\S]*\})', response_text)
                    if json_match:
                        json_str = json_match.group(1)
                    else:
                        json_str = response_text
                
                topics = json.loads(json_str)
                
                # Validate the format
                if not isinstance(topics, dict):
                    raise ValueError("Response is not a JSON object")
                
                if "blog_topics" not in topics or "linkedin_topics" not in topics or "twitter_topics" not in topics:
                    raise ValueError("Missing required topic arrays in response")
                
                return {
                    "success": True,
                    "topics": topics
                }
            
            except (json.JSONDecodeError, ValueError) as e:
                # If JSON parsing fails, format the text response ourselves
                logging.error(f"Failed to parse JSON from response: {str(e)}")
                
                # Process text response into structured format
                return {
                    "success": False,
                    "error": f"Failed to parse topics into JSON format: {str(e)}",
                    "raw_response": response.text
                }
        else:
            return {
                "success": False,
                "error": "Failed to generate topics. Empty or invalid response from Gemini."
            }
    
    except Exception as e:
        logging.error(f"Error during topic generation: {str(e)}")
        return {
            "success": False,
            "error": f"Topic generation error: {str(e)}"
        }

def generate_blog_post(topic, transcript):
    """
    Generates a blog post based on a topic and transcript.
    
    Args:
        topic (dict): The topic information with title and description
        transcript (str): The refined transcript text
        
    Returns:
        dict: A dictionary with generation result and blog post if successful
    """
    if not topic or not transcript:
        return {
            "success": False,
            "error": "Missing required inputs (topic or transcript)."
        }
    
    logging.info(f"Generating blog post for topic: {topic.get('title', 'Unknown')}")
    
    try:
        # Use Gemini to generate the blog post
        gemini_model = genai.GenerativeModel(model_name="gemini-1.5-pro", temperature=0.7)
        
        prompt = f"""
        Create a professional, informative blog post of up to 500 words based on the following topic and transcript.
        
        Topic: {topic.get('title', 'Unknown')}
        Topic Description: {topic.get('description', 'No description provided')}
        
        Use information from this transcript:
        {transcript[:5000]}  # Limit transcript length to avoid hitting token limits
        
        The blog post should:
        - Have a clear structure with introduction, body, and conclusion
        - Include 2-3 main points or insights from the transcript
        - Be written in a professional but conversational tone
        - Include a strong headline
        - End with a brief call-to-action or concluding thought
        
        Format the blog post with proper headings, paragraphs, and spacing.
        """
        
        response = gemini_model.generate_content(prompt)
        
        if response and hasattr(response, 'text'):
            blog_post = response.text.strip()
            
            # Verify word count
            word_count = len(blog_post.split())
            if word_count > 550:  # Allow a small buffer over 500
                logging.warning(f"Blog post exceeds 500 words (actual: {word_count}). It may need editing.")
            
            return {
                "success": True,
                "topic": topic.get('title', 'Unknown'),
                "content": blog_post,
                "word_count": word_count
            }
        else:
            return {
                "success": False,
                "error": "Failed to generate blog post. Empty or invalid response from Gemini."
            }
    
    except Exception as e:
        logging.error(f"Error during blog post generation: {str(e)}")
        return {
            "success": False,
            "error": f"Blog post generation error: {str(e)}"
        }

def generate_twitter_post(topic, transcript):
    """
    Generates a Twitter post based on a topic and transcript.
    
    Args:
        topic (dict): The topic information with title and description
        transcript (str): The refined transcript text
        
    Returns:
        dict: A dictionary with generation result and Twitter post if successful
    """
    if not topic or not transcript:
        return {
            "success": False,
            "error": "Missing required inputs (topic or transcript)."
        }
    
    logging.info(f"Generating Twitter post for topic: {topic.get('title', 'Unknown')}")
    
    try:
        # Use Gemini to generate the Twitter post
        gemini_model = genai.GenerativeModel(model_name="gemini-1.5-pro", temperature=0.7)
        
        prompt = f"""
        Create a concise Twitter post of up to 280 characters based on the following topic and transcript.
        
        Topic: {topic.get('title', 'Unknown')}
        Topic Description: {topic.get('description', 'No description provided')}
        
        Use information from this transcript:
        {transcript[:2000]}  # Limit transcript length to avoid hitting token limits
        
        The Twitter post should:
        - Begin with a hook that grabs attention
        - Focus on a single clear takeaway or insight
        - Use simple, direct language
        - Include 1-2 relevant hashtags if space permits
        - Leave some character space for comments when shared
        
        The post MUST be 280 characters or less.
        """
        
        response = gemini_model.generate_content(prompt)
        
        if response and hasattr(response, 'text'):
            twitter_post = response.text.strip()
            
            # Verify character count
            char_count = len(twitter_post)
            if char_count > 280:
                logging.warning(f"Twitter post exceeds 280 characters (actual: {char_count}). Truncating.")
                twitter_post = twitter_post[:277] + "..."
                char_count = len(twitter_post)
            
            return {
                "success": True,
                "topic": topic.get('title', 'Unknown'),
                "content": twitter_post,
                "char_count": char_count
            }
        else:
            return {
                "success": False,
                "error": "Failed to generate Twitter post. Empty or invalid response from Gemini."
            }
    
    except Exception as e:
        logging.error(f"Error during Twitter post generation: {str(e)}")
        return {
            "success": False,
            "error": f"Twitter post generation error: {str(e)}"
        }

def edit_blog_post(blog_post):
    """
    Edits and refines a blog post for grammar, accuracy, and style.
    
    Args:
        blog_post (dict): The blog post content and metadata
        
    Returns:
        dict: A dictionary with editing result and edited blog post if successful
    """
    if not blog_post or "content" not in blog_post:
        return {
            "success": False,
            "error": "Missing required input (blog post content)."
        }
    
    logging.info(f"Editing blog post: {blog_post.get('topic', 'Unknown')}")
    
    try:
        # Use Gemini to edit the blog post
        gemini_model = genai.GenerativeModel(model_name="gemini-1.5-pro", temperature=0.2)
        
        prompt = f"""
        Edit and improve the following blog post for grammar, clarity, style, and overall quality.
        Ensure it remains under 500 words and maintains a professional yet conversational tone.
        Verify that the structure is logical, with clear headings, introduction, and conclusion.
        Fix any factual errors or inconsistencies.
        
        Blog Post:
        {blog_post['content']}
        
        Provide the complete edited version of the blog post.
        """
        
        response = gemini_model.generate_content(prompt)
        
        if response and hasattr(response, 'text'):
            edited_post = response.text.strip()
            
            # Verify word count
            word_count = len(edited_post.split())
            if word_count > 550:  # Allow a small buffer over 500
                logging.warning(f"Edited blog post exceeds 500 words (actual: {word_count}). It may need further editing.")
            
            return {
                "success": True,
                "topic": blog_post.get('topic', 'Unknown'),
                "original_content": blog_post['content'],
                "edited_content": edited_post,
                "word_count": word_count
            }
        else:
            return {
                "success": False,
                "error": "Failed to edit blog post. Empty or invalid response from Gemini."
            }
    
    except Exception as e:
        logging.error(f"Error during blog post editing: {str(e)}")
        return {
            "success": False,
            "error": f"Blog post editing error: {str(e)}"
        }

def edit_linkedin_post(linkedin_post):
    """
    Edits and refines a LinkedIn post for grammar, accuracy, and style.
    
    Args:
        linkedin_post (dict): The LinkedIn post content and metadata
        
    Returns:
        dict: A dictionary with editing result and edited LinkedIn post if successful
    """
    if not linkedin_post or "content" not in linkedin_post:
        return {
            "success": False,
            "error": "Missing required input (LinkedIn post content)."
        }
    
    logging.info(f"Editing LinkedIn post: {linkedin_post.get('topic', 'Unknown')}")
    
    try:
        # Use Gemini to edit the LinkedIn post
        gemini_model = genai.GenerativeModel(model_name="gemini-1.5-pro", temperature=0.2)
        
        prompt = f"""
        Edit and improve the following LinkedIn post for grammar, clarity, style, and overall quality.
        Ensure it remains under 100 words and maintains a professional tone appropriate for LinkedIn.
        Check that it has a strong opening, clear message, and effective call-to-action.
        Verify that hashtags are relevant and properly formatted.
        
        LinkedIn Post:
        {linkedin_post['content']}
        
        Provide the complete edited version of the LinkedIn post.
        """
        
        response = gemini_model.generate_content(prompt)
        
        if response and hasattr(response, 'text'):
            edited_post = response.text.strip()
            
            # Verify word count
            word_count = len(edited_post.split())
            if word_count > 110:  # Allow a small buffer over 100
                logging.warning(f"Edited LinkedIn post exceeds 100 words (actual: {word_count}). It may need further editing.")
            
            return {
                "success": True,
                "topic": linkedin_post.get('topic', 'Unknown'),
                "original_content": linkedin_post['content'],
                "edited_content": edited_post,
                "word_count": word_count
            }
        else:
            return {
                "success": False,
                "error": "Failed to edit LinkedIn post. Empty or invalid response from Gemini."
            }
    
    except Exception as e:
        logging.error(f"Error during LinkedIn post editing: {str(e)}")
        return {
            "success": False,
            "error": f"LinkedIn post editing error: {str(e)}"
        }

def edit_twitter_post(twitter_post):
    """
    Edits and refines a Twitter post for grammar, accuracy, and impact.
    
    Args:
        twitter_post (dict): The Twitter post content and metadata
        
    Returns:
        dict: A dictionary with editing result and edited Twitter post if successful
    """
    if not twitter_post or "content" not in twitter_post:
        return {
            "success": False,
            "error": "Missing required input (Twitter post content)."
        }
    
    logging.info(f"Editing Twitter post: {twitter_post.get('topic', 'Unknown')}")
    
    try:
        # Use Gemini to edit the Twitter post
        gemini_model = genai.GenerativeModel(model_name="gemini-1.5-pro", temperature=0.2)
        
        prompt = f"""
        Edit and improve the following Twitter post for grammar, clarity, impact, and overall quality.
        Ensure it remains under 280 characters and has a strong, engaging message.
        Make sure every word serves a purpose and the language is concise and direct.
        
        Twitter Post:
        {twitter_post['content']}
        
        Provide the complete edited version of the Twitter post.
        """
        
        response = gemini_model.generate_content(prompt)
        
        if response and hasattr(response, 'text'):
            edited_post = response.text.strip()
            
            # Verify character count
            char_count = len(edited_post)
            if char_count > 280:
                logging.warning(f"Edited Twitter post exceeds 280 characters (actual: {char_count}). Truncating.")
                edited_post = edited_post[:277] + "..."
                char_count = len(edited_post)
            
            return {
                "success": True,
                "topic": twitter_post.get('topic', 'Unknown'),
                "original_content": twitter_post['content'],
                "edited_content": edited_post,
                "char_count": char_count
            }
        else:
            return {
                "success": False,
                "error": "Failed to edit Twitter post. Empty or invalid response from Gemini."
            }
    
    except Exception as e:
        logging.error(f"Error during Twitter post editing: {str(e)}")
        return {
            "success": False,
            "error": f"Twitter post editing error: {str(e)}"
        }

def save_output(content_data, output_file="repurposed_content.txt"):
    """
    Saves all repurposed content to a text file.
    
    Args:
        content_data (dict): Dictionary containing all repurposed content
        output_file (str): The filename to save the content to
        
    Returns:
        dict: A dictionary with saving result and file path if successful
    """
    if not content_data:
        return {
            "success": False,
            "error": "No content data provided to save."
        }
    
    logging.info(f"Saving repurposed content to {output_file}")
    
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            # Write header
            f.write("# REPURPOSED CONTENT FROM YOUTUBE VIDEO\n\n")
            
            # Write video information if available
            if "video_info" in content_data:
                f.write(f"## Original Video Information\n")
                f.write(f"Title: {content_data['video_info'].get('title', 'Unknown')}\n")
                f.write(f"Channel: {content_data['video_info'].get('channel', 'Unknown')}\n")
                f.write(f"Published Date: {content_data['video_info'].get('published_date', 'Unknown')}\n")
                f.write(f"URL: {content_data.get('video_url', 'Unknown')}\n\n")
            
            # Write blog posts
            if "blog_posts" in content_data and content_data["blog_posts"]:
                f.write(f"## BLOG POSTS\n\n")
                for i, post in enumerate(content_data["blog_posts"], 1):
                    f.write(f"### Blog Post {i}: {post.get('topic', 'Untitled')}\n\n")
                    f.write(f"{post.get('edited_content', post.get('content', 'No content'))}\n\n")
                    f.write(f"Word count: {post.get('word_count', 'Unknown')}\n\n")
                    f.write("----------\n\n")
            
            # Write LinkedIn posts
            if "linkedin_posts" in content_data and content_data["linkedin_posts"]:
                f.write(f"## LINKEDIN POSTS\n\n")
                for i, post in enumerate(content_data["linkedin_posts"], 1):
                    f.write(f"### LinkedIn Post {i}: {post.get('topic', 'Untitled')}\n\n")
                    f.write(f"{post.get('edited_content', post.get('content', 'No content'))}\n\n")
                    f.write(f"Word count: {post.get('word_count', 'Unknown')}\n\n")
                    f.write("----------\n\n")
            
            # Write Twitter posts
            if "twitter_posts" in content_data and content_data["twitter_posts"]:
                f.write(f"## TWITTER POSTS\n\n")
                for i, post in enumerate(content_data["twitter_posts"], 1):
                    f.write(f"### Twitter Post {i}: {post.get('topic', 'Untitled')}\n\n")
                    f.write(f"{post.get('edited_content', post.get('content', 'No content'))}\n\n")
                    f.write(f"Character count: {post.get('char_count', 'Unknown')}\n\n")
                    f.write("----------\n\n")
        
        return {
            "success": True,
            "file_path": os.path.abspath(output_file),
            "message": f"Successfully saved repurposed content to {output_file}"
        }
    
    except Exception as e:
        logging.error(f"Error saving output file: {str(e)}")
        return {
            "success": False,
            "error": f"Failed to save output file: {str(e)}"
        }

def generate_linkedin_post(topic, transcript):
    """
    Generates a LinkedIn post based on a topic and transcript.
    
    Args:
        topic (dict): The topic information with title and description
        transcript (str): The refined transcript text
        
    Returns:
        dict: A dictionary with generation result and LinkedIn post if successful
    """
    if not topic or not transcript:
        return {
            "success": False,
            "error": "Missing required inputs (topic or transcript)."
        }
    
    logging.info(f"Generating LinkedIn post for topic: {topic.get('title', 'Unknown')}")
    
    try:
        # Use Gemini to generate the LinkedIn post
        gemini_model = genai.GenerativeModel(model_name="gemini-1.5-pro", temperature=0.7)
        
        prompt = f"""
        Create a professional LinkedIn post of up to 100 words based on the following topic and transcript.
        
        Topic: {topic.get('title', 'Unknown')}
        Topic Description: {topic.get('description', 'No description provided')}
        
        Use information from this transcript:
        {transcript[:3000]}  # Limit transcript length to avoid hitting token limits
        
        The LinkedIn post should:
        - Begin with a strong opening line that grabs attention
        - Focus on one key insight or takeaway
        - Be written in a professional, conversational tone
        - Use short paragraphs (1-2 sentences)
        - Include a thought-provoking question or call-to-action
        - End with 3-5 relevant hashtags
        
        Format the post with appropriate line breaks for readability on LinkedIn.
        """
        
        response = gemini_model.generate_content(prompt)
        
        if response and hasattr(response, 'text'):
            linkedin_post = response.text.strip()
            
            # Verify word count
            word_count = len(linkedin_post.split())
            if word_count > 110:  # Allow a small buffer over 100
                logging.warning(f"LinkedIn post exceeds 100 words (actual: {word_count}). It may need editing.")
            
            return {
                "success": True,
                "topic": topic.get('title', 'Unknown'),
                "content": linkedin_post,
                "word_count": word_count
            }
        else:
            return {
                "success": False,
                "error": "Failed to generate LinkedIn post. Empty or invalid response from Gemini."
            }
    
    except Exception as e:
        logging.error(f"Error during LinkedIn post generation: {str(e)}")
        return {
            "success": False,
            "error": f"LinkedIn post generation error: {str(e)}"
        }