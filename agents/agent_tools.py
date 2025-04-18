import os
import json
import re
import time
import logging
from apify_client import ApifyClient
import google.generativeai as genai
from dotenv import load_dotenv
from openai import OpenAI

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Load environment variables
load_dotenv()

# Initialize DeepSeek client
deepseek_client = OpenAI(
    api_key=os.getenv('DEEPSEEK_API_KEY'),
    base_url="https://api.deepseek.com/v1"
)

# Initialize Apify client
apify_api_key = os.getenv('APIFY_API_KEY')
gemini_api_key = os.getenv('GEMINI_API_KEY')

if not apify_api_key:
    raise ValueError("APIFY_API_KEY is not set in the .env file.")
if not gemini_api_key:
    raise ValueError("GEMINI_API_KEY is not set in the .env file.")

apify_client = ApifyClient(apify_api_key)
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
        run = apify_client.actor("1s7eXiaukVuOr4Ueg").call(run_input=run_input)
        
        # Check the run status
        run_info = apify_client.run(run["id"]).get()
        
        # Wait for completion with a timeout
        max_wait_time = 600  # 10 minutes timeout for longer videos
        start_time = time.time()
        
        while run_info['status'] in ['RUNNING', 'READY']:
            if time.time() - start_time > max_wait_time:
                return {
                    "success": False,
                    "error": "Extraction timeout. The operation took too long to complete."
                }
            
            logging.info(f"Current status: {run_info['status']}. Waiting...")
            time.sleep(5)
            run_info = apify_client.run(run["id"]).get()
        
        if run_info['status'] == 'SUCCEEDED':
            logging.info(f"Actor run completed successfully. Dataset ID: {run['defaultDatasetId']}")
            
            # Fetch results from the dataset
            items = list(apify_client.dataset(run["defaultDatasetId"]).iterate_items())
            
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
            captions_list = video_data.get('captions', [])
            
            if captions_list:
                logging.info(f"Attempting to join {len(captions_list)} caption items.")
                try:
                    # Join captions and clean up
                    transcript_text = " ".join(captions_list)
                    # Clean up any HTML entities and extra spaces
                    transcript_text = transcript_text.replace('&#39;', "'")
                    transcript_text = re.sub(r'\s+', ' ', transcript_text).strip()
                    logging.info("Successfully joined captions.")
                except Exception as join_err:
                    logging.error(f"Error joining captions list: {join_err}")
                    transcript_text = ""
            else:
                logging.warning("Captions list is empty after retrieving from video_data.")

            # Log final text using WARNING level BEFORE the check
            logging.warning(f"Transcript passed to refinement (first 500 chars): '{transcript_text[:500]}'")
            
            # Check if transcript is empty OR whitespace only
            if not transcript_text or not transcript_text.strip():
                logging.error("Failed to process captions into non-empty transcript text.")
                return {
                    "success": False,
                    "error": "Failed to process captions into transcript (empty or whitespace only)"
                }
            
            # Return successful result with transcript and video info
            return {
                "success": True,
                "video_info": {
                    "title": video_data.get('title', 'Unknown Title'),
                    "channel": video_data.get('channelName', 'Unknown Channel'),
                    "published_date": video_data.get('datePublished', 'Unknown Date')
                },
                "transcript": transcript_text,
                "raw_data": video_data  # Keep raw data for debugging if needed
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

def call_deepseek_with_retry(prompt, max_retries=3, initial_wait=2):
    """
    Call DeepSeek API with retry logic for rate limits.
    """
    for attempt in range(1, max_retries + 1):
        try:
            response = deepseek_client.chat.completions.create(
                model="deepseek-chat",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,
                max_tokens=2048
            )
            return response.choices[0].message.content
        except Exception as e:
            if attempt == max_retries:
                logging.error(f"Failed after {max_retries} attempts: {str(e)}")
                raise
            wait_time = initial_wait * (2 ** (attempt - 1))
            logging.info(f"Retry attempt {attempt}/{max_retries}. Waiting {wait_time} seconds...")
            time.sleep(wait_time)

def refine_transcript(transcript):
    """
    Refines a transcript using DeepSeek to fix errors and improve quality.
    """
    if not transcript:
        return {
            "success": False,
            "error": "No transcript provided"
        }

    try:
        logging.info("Refining transcript with DeepSeek...")
        
        # Prepare the prompt
        prompt = f"""
        Please refine this transcript to improve readability and clarity.
        Fix any grammar, punctuation, or formatting issues while preserving the original meaning.
        
        Transcript:
        {transcript[:3000]}  # Limit length to avoid token limits
        
        Return only the refined text without any additional comments.
        """
        
        refined_transcript = call_deepseek_with_retry(prompt)
        
        if refined_transcript:
            return {
                "success": True,
                "refined_transcript": refined_transcript.strip()
            }
        else:
            return {
                "success": False,
                "error": "Failed to generate refined transcript. Empty or invalid response from DeepSeek."
            }
            
    except Exception as e:
        logging.error(f"Error during transcript refinement: {str(e)}")
        return {
            "success": False,
            "error": f"Refinement error: {str(e)}"
        }

def generate_content_topics(transcript, content_type="all"):
    """
    Generate content topics based on the transcript.
    Handles longer transcripts by processing them in chunks.
    """
    try:
        logging.info("Generating content topics with DeepSeek...")
        
        # Split transcript into chunks of 2000 characters with 200 char overlap
        chunk_size = 2000
        overlap = 200
        chunks = []
        
        for i in range(0, len(transcript), chunk_size - overlap):
            chunk = transcript[i:i + chunk_size]
            chunks.append(chunk)
            if len(chunks) >= 3:  # Limit to first 3 chunks (6000 chars) to avoid too many API calls
                break
        
        all_topics = []
        for chunk in chunks:
            prompt = f"""
            Based on this part of the transcript, generate content topics according to these requirements:
            - 1 blog post topic (informative, detailed content up to 500 words)
            - 2 LinkedIn post topics (professional, insightful content up to 100 words)
            - 5 Twitter post topics (concise, engaging content up to 280 characters)
            
            Return your response in this exact JSON format:
            [
                {{
                    "title": "Catchy Title Here",
                    "description": "Brief description of the topic",
                    "key_points": ["Point 1", "Point 2", "Point 3"],
                    "target_audience": "Description of target audience",
                    "platform": "blog|linkedin|twitter"
                }}
            ]
            
            Make sure to:
            1. Use proper JSON formatting with double quotes for strings
            2. Include exactly these fields: title, description, key_points (as array), target_audience, platform
            3. Return only the JSON array, no other text
            4. Focus on unique topics not covered in previous chunks
            5. Ensure each topic is appropriate for its target platform
            
            Transcript chunk:
            {chunk}
            """
            
            response = call_deepseek_with_retry(prompt)
            
            if response:
                try:
                    # Clean the response to handle potential markdown formatting
                    cleaned_response = response.strip().strip('`').strip()
                    if cleaned_response.startswith('json'):
                        cleaned_response = cleaned_response[4:].strip()
                    
                    chunk_topics = json.loads(cleaned_response)
                    all_topics.extend(chunk_topics)
                except json.JSONDecodeError as e:
                    logging.error(f"JSON Parse Error for chunk: {str(e)}")
                    logging.error(f"Raw Response: {response}")
                    continue
        
        if all_topics:
            # Filter and limit topics by platform
            blog_topics = [t for t in all_topics if t.get("platform") == "blog"][:1]
            linkedin_topics = [t for t in all_topics if t.get("platform") == "linkedin"][:2]
            twitter_topics = [t for t in all_topics if t.get("platform") == "twitter"][:5]
            
            # Combine filtered topics
            filtered_topics = blog_topics + linkedin_topics + twitter_topics
            
            return {
                "success": True,
                "topics": filtered_topics
            }
        else:
            return {
                "success": False,
                "error": "Failed to generate any valid topics from the transcript chunks."
            }
            
    except Exception as e:
        logging.error(f"Error during topic generation: {str(e)}")
        return {
            "success": False,
            "error": f"Topic generation error: {str(e)}"
        }

def generate_blog_post(topic, transcript):
    """
    Generate a blog post based on the topic and transcript.
    For longer transcripts, it searches for relevant sections to use as context.
    """
    try:
        # First, find the most relevant chunk of the transcript for this topic
        search_prompt = f"""
        Rate how relevant this transcript chunk is to the following topic on a scale of 1-5:
        
        Topic:
        {json.dumps(topic, indent=2)}
        
        Transcript chunk:
        {transcript[:2000]}
        
        Return ONLY a single number 1-5, where 5 is most relevant.
        """
        
        relevance_response = call_deepseek_with_retry(prompt=search_prompt)
        # Extract just the first number from the response
        relevance_score = int(''.join(filter(str.isdigit, relevance_response[:2])) or "1")
        
        # If first chunk isn't very relevant (score < 3), check middle and end chunks
        if relevance_score < 3 and len(transcript) > 4000:
            mid_point = len(transcript) // 2
            mid_chunk = transcript[mid_point-1000:mid_point+1000]
            end_chunk = transcript[-2000:]
            
            mid_response = call_deepseek_with_retry(
                prompt=search_prompt.replace(transcript[:2000], mid_chunk)
            )
            mid_score = int(''.join(filter(str.isdigit, mid_response[:2])) or "1")
            
            end_response = call_deepseek_with_retry(
                prompt=search_prompt.replace(transcript[:2000], end_chunk)
            )
            end_score = int(''.join(filter(str.isdigit, end_response[:2])) or "1")
            
            # Use the most relevant chunk
            if mid_score > relevance_score and mid_score > end_score:
                transcript_chunk = mid_chunk
            elif end_score > relevance_score and end_score > mid_score:
                transcript_chunk = end_chunk
            else:
                transcript_chunk = transcript[:2000]
        else:
            transcript_chunk = transcript[:2000]
        
        prompt = f"""
        Create a blog post (max 500 words) based on this topic and transcript chunk.
        If the chunk seems incomplete or you need more context, focus on the aspects you can confidently write about.
        
        Topic:
        {json.dumps(topic, indent=2)}
        
        Transcript chunk to focus on:
        {transcript_chunk}
        
        Guidelines:
        - Start with a clear title using markdown heading (# Title)
        - Engaging introduction
        - Clear structure with subheadings
        - Professional tone
        - Actionable insights
        - Strong conclusion
        - If the chunk feels incomplete, acknowledge any limitations in coverage
        
        Return the blog post with proper markdown formatting.
        """
        
        blog_content = call_deepseek_with_retry(prompt)
        
        if blog_content:
            return {
                "success": True,
                "content": blog_content.strip(),
                "topic": topic["title"]
            }
        else:
            return {
                "success": False,
                "error": "Failed to generate blog post. Empty or invalid response from DeepSeek."
            }
            
    except Exception as e:
        logging.error(f"Error during blog post generation: {str(e)}")
        return {
            "success": False,
            "error": f"Blog generation error: {str(e)}"
        }

def generate_twitter_post(topic, transcript):
    """
    Generate a Twitter post based on the topic and transcript.
    """
    try:
        prompt = f"""
        Create an engaging tweet (max 280 characters) based on this topic and transcript.
        
        Topic:
        {json.dumps(topic, indent=2)}
        
        Reference material:
        {transcript[:1000]}
        
        Guidelines:
        - Attention-grabbing
        - Clear message
        - Include hashtags
        - Encourage engagement
        
        Return only the tweet text.
        """
        
        tweet_content = call_deepseek_with_retry(prompt)
        
        if tweet_content:
            # Ensure tweet length
            tweet = tweet_content.strip()
            if len(tweet) > 280:
                tweet = tweet[:277] + "..."
                
            return {
                "success": True,
                "content": tweet,
                "topic": topic["title"]
            }
        else:
            return {
                "success": False,
                "error": "Failed to generate Twitter post. Empty or invalid response from DeepSeek."
            }
            
    except Exception as e:
        logging.error(f"Error during Twitter post generation: {str(e)}")
        return {
            "success": False,
            "error": f"Twitter generation error: {str(e)}"
        }

def edit_blog_post(post_content):
    """
    Edit and improve a blog post.
    """
    try:
        prompt = f"""
        Edit and improve this blog post while maintaining its core message.
        Focus on:
        - Clarity and flow
        - Grammar and style
        - Engagement
        - Professional tone
        
        Blog post:
        {post_content}
        
        Return the edited post only.
        """
        
        edited_content = call_deepseek_with_retry(prompt)
        
        if edited_content:
            return {
                "success": True,
                "edited_content": edited_content.strip()
            }
        else:
            return {
                "success": False,
                "error": "Failed to edit blog post. Empty or invalid response from DeepSeek."
            }
            
    except Exception as e:
        logging.error(f"Error during blog post editing: {str(e)}")
        return {
            "success": False,
            "error": f"Blog editing error: {str(e)}"
        }

def edit_linkedin_post(post_content):
    """
    Edit and improve a LinkedIn post.
    """
    try:
        prompt = f"""
        Edit and improve this LinkedIn post while maintaining its core message.
        Focus on:
        - Professional tone
        - Clear value proposition
        - Engagement
        - Appropriate hashtags
        
        Post:
        {post_content}
        
        Return the edited post only.
        """
        
        edited_content = call_deepseek_with_retry(prompt)
        
        if edited_content:
            return {
                "success": True,
                "edited_content": edited_content.strip()
            }
        else:
            return {
                "success": False,
                "error": "Failed to edit LinkedIn post. Empty or invalid response from DeepSeek."
            }
            
    except Exception as e:
        logging.error(f"Error during LinkedIn post editing: {str(e)}")
        return {
            "success": False,
            "error": f"LinkedIn editing error: {str(e)}"
        }

def edit_twitter_post(post_content):
    """
    Edit and improve a Twitter post.
    """
    try:
        prompt = f"""
        Edit and improve this tweet while maintaining its core message.
        Ensure it's within 280 characters.
        Focus on:
        - Impact and clarity
        - Engagement
        - Appropriate hashtags
        
        Tweet:
        {post_content}
        
        Return the edited tweet only.
        """
        
        edited_content = call_deepseek_with_retry(prompt)
        
        if edited_content:
            tweet = edited_content.strip()
            if len(tweet) > 280:
                tweet = tweet[:277] + "..."
                
            return {
                "success": True,
                "edited_content": tweet
            }
        else:
            return {
                "success": False,
                "error": "Failed to edit Twitter post. Empty or invalid response from DeepSeek."
            }
            
    except Exception as e:
        logging.error(f"Error during Twitter post editing: {str(e)}")
        return {
            "success": False,
            "error": f"Twitter editing error: {str(e)}"
        }

def generate_linkedin_post(topic, transcript):
    """
    Generate a LinkedIn post based on the topic and transcript.
    """
    try:
        prompt = f"""
        Create a LinkedIn post (max 100 words) based on this topic and transcript.
        
        Topic:
        {json.dumps(topic, indent=2)}
        
        Reference material:
        {transcript[:1500]}
        
        Guidelines:
        - Professional tone
        - Clear value proposition
        - Include relevant hashtags
        - Call to action
        
        Return only the post text.
        """
        
        post_content = call_deepseek_with_retry(prompt)
        
        if post_content:
            return {
                "success": True,
                "content": post_content.strip(),
                "topic": topic["title"]
            }
        else:
            return {
                "success": False,
                "error": "Failed to generate LinkedIn post. Empty or invalid response from DeepSeek."
            }
            
    except Exception as e:
        logging.error(f"Error during LinkedIn post generation: {str(e)}")
        return {
            "success": False,
            "error": f"LinkedIn generation error: {str(e)}"
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
                    # Extract title from the content if it starts with a markdown heading
                    content = post.get('edited_content', post.get('content', ''))
                    title = None
                    
                    # Try to find the title in the content
                    lines = content.split('\n')
                    for line in lines:
                        if line.strip().startswith('# '):
                            title = line.strip('# ').strip()
                            break
                    
                    if not title:
                        title = post.get('topic', 'Untitled')
                    
                    f.write(f"### Blog Post {i}: {title}\n\n")
                    f.write(f"{content}\n\n")
                    # Calculate word count
                    word_count = len(content.split())
                    f.write(f"Word count: {word_count}\n\n")
                    f.write("----------\n\n")
            
            # Write LinkedIn posts
            if "linkedin_posts" in content_data and content_data["linkedin_posts"]:
                f.write(f"## LINKEDIN POSTS\n\n")
                for i, post in enumerate(content_data["linkedin_posts"], 1):
                    content = post.get('edited_content', post.get('content', ''))
                    
                    # Try to extract title from content (usually in bold at the start)
                    title = None
                    lines = content.split('\n')
                    for line in lines:
                        if line.strip().startswith('**') and line.strip().endswith('**'):
                            title = line.strip('**').strip()
                            break
                    
                    if not title:
                        title = post.get('topic', 'Untitled')
                    
                    f.write(f"### LinkedIn Post {i}: {title}\n\n")
                    f.write(f"{content}\n\n")
                    word_count = len(content.split())
                    f.write(f"Word count: {word_count}\n\n")
                    f.write("----------\n\n")
            
            # Write Twitter posts
            if "twitter_posts" in content_data and content_data["twitter_posts"]:
                f.write(f"## TWITTER POSTS\n\n")
                for i, post in enumerate(content_data["twitter_posts"], 1):
                    content = post.get('edited_content', post.get('content', ''))
                    
                    # For Twitter, use the first line as title if it's in quotes
                    title = None
                    if content.strip().startswith('"'):
                        title_end = content.find('"', 1)
                        if title_end != -1:
                            title = content[1:title_end]
                    
                    if not title:
                        title = post.get('topic', 'Untitled')
                    
                    f.write(f"### Twitter Post {i}: {title}\n\n")
                    f.write(f"{content}\n\n")
                    char_count = len(content)
                    f.write(f"Character count: {char_count}\n\n")
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

def _generate_platform_content(self, platform):
    """Generate content for a specific platform."""
    logging.info(f"Generating {platform} content")
    
    # Filter topics by platform
    platform_topics = [t for t in self.content_data["topics"] if t.get("platform") == platform]
    
    # Set limits for each platform
    limits = {
        "blog": 1,
        "linkedin": 2,
        "twitter": 5
    }
    
    # Use only the required number of topics
    topics_to_use = platform_topics[:limits[platform]]
    
    for topic in topics_to_use:
        # Generate content
        if platform == "blog":
            result = generate_blog_post(topic, self.content_data["refined_transcript"])
        elif platform == "linkedin":
            result = generate_linkedin_post(topic, self.content_data["refined_transcript"])
        elif platform == "twitter":
            result = generate_twitter_post(topic, self.content_data["refined_transcript"])
        else:
            continue
        
        if not result.get("success", False):
            logging.warning(f"Failed to generate {platform} content for topic: {topic.get('title', 'Unknown')}")
            continue
        
        # Edit content
        if platform == "blog":
            edit_result = edit_blog_post(result["content"])
        elif platform == "linkedin":
            edit_result = edit_linkedin_post(result["content"])
        elif platform == "twitter":
            edit_result = edit_twitter_post(result["content"])
        else:
            edit_result = result
        
        if not edit_result.get("success", False):
            logging.warning(f"Failed to edit {platform} content for topic: {topic.get('title', 'Unknown')}")
            edit_result = result
        
        # Store the content
        self.content_data[f"{platform}_posts"].append(edit_result)