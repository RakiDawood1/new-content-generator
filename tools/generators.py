import os
import json
import logging
import google.generativeai as genai
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Load environment variables
load_dotenv()

# Get API key from environment variables
gemini_api_key = os.getenv('GEMINI_API_KEY')

# Configure Gemini API
if not gemini_api_key:
    raise ValueError("GEMINI_API_KEY is not set in the .env file.")

genai.configure(api_key=gemini_api_key)

def analyze_transcript_content(transcript):
    """
    Analyze transcript content to identify key themes and topics.
    
    Args:
        transcript (str): The refined transcript text
        
    Returns:
        dict: Dictionary containing analysis results
    """
    try:
        # Create Gemini model instance for analysis
        gemini_model = genai.GenerativeModel(model_name="gemini-1.5-pro", temperature=0.3)
        
        # Prepare the analysis prompt
        prompt = f"""
        Analyze this transcript and identify:
        1. Main themes and topics
        2. Key insights and takeaways
        3. Notable quotes or statements
        4. Target audience interests
        5. Content opportunities
        
        Format the response as JSON with these keys:
        - themes: list of main themes
        - insights: list of key insights
        - quotes: list of notable quotes
        - audience: list of audience interests
        - opportunities: list of content opportunities
        
        Transcript:
        {transcript[:4000]}  # Limit length to avoid token limits
        """
        
        response = gemini_model.generate_content(prompt)
        
        if response and hasattr(response, 'text'):
            try:
                analysis = json.loads(response.text)
                return {
                    "success": True,
                    "analysis": analysis
                }
            except json.JSONDecodeError:
                return {
                    "success": False,
                    "error": "Failed to parse analysis results"
                }
        else:
            return {
                "success": False,
                "error": "Failed to get valid response from Gemini"
            }
    
    except Exception as e:
        logging.error(f"Error during content analysis: {str(e)}")
        return {
            "success": False,
            "error": f"Analysis error: {str(e)}"
        }

def generate_blog_topics(analysis, count=5):
    """
    Generate blog post topics based on content analysis.
    
    Args:
        analysis (dict): Content analysis results
        count (int): Number of topics to generate
        
    Returns:
        dict: Dictionary containing blog topics
    """
    try:
        # Create Gemini model instance
        gemini_model = genai.GenerativeModel(model_name="gemini-1.5-pro", temperature=0.7)
        
        # Prepare the generation prompt
        prompt = f"""
        Based on this content analysis, generate {count} blog post topics.
        Each topic should:
        1. Be specific and focused
        2. Address key insights or themes
        3. Be suitable for a 500-word blog post
        4. Include a clear value proposition
        5. Have an engaging headline
        
        Format each topic as a JSON object with:
        - title: The blog post headline
        - description: Brief description of the content angle
        - key_points: 2-3 main points to cover
        
        Analysis:
        {json.dumps(analysis, indent=2)}
        """
        
        response = gemini_model.generate_content(prompt)
        
        if response and hasattr(response, 'text'):
            try:
                topics = json.loads(response.text)
                return {
                    "success": True,
                    "topics": topics
                }
            except json.JSONDecodeError:
                return {
                    "success": False,
                    "error": "Failed to parse generated topics"
                }
        else:
            return {
                "success": False,
                "error": "Failed to get valid response from Gemini"
            }
    
    except Exception as e:
        logging.error(f"Error during blog topic generation: {str(e)}")
        return {
            "success": False,
            "error": f"Topic generation error: {str(e)}"
        }

def generate_linkedin_topics(analysis, count=5):
    """
    Generate LinkedIn post topics based on content analysis.
    
    Args:
        analysis (dict): Content analysis results
        count (int): Number of topics to generate
        
    Returns:
        dict: Dictionary containing LinkedIn topics
    """
    try:
        # Create Gemini model instance
        gemini_model = genai.GenerativeModel(model_name="gemini-1.5-pro", temperature=0.7)
        
        # Prepare the generation prompt
        prompt = f"""
        Based on this content analysis, generate {count} LinkedIn post topics.
        Each topic should:
        1. Be professional and insightful
        2. Focus on business value or career relevance
        3. Be suitable for a 100-word LinkedIn post
        4. Include a conversation starter
        5. Suggest relevant hashtags
        
        Format each topic as a JSON object with:
        - title: The post's main message
        - description: Brief description of the angle
        - hashtags: 3-5 relevant hashtags
        
        Analysis:
        {json.dumps(analysis, indent=2)}
        """
        
        response = gemini_model.generate_content(prompt)
        
        if response and hasattr(response, 'text'):
            try:
                topics = json.loads(response.text)
                return {
                    "success": True,
                    "topics": topics
                }
            except json.JSONDecodeError:
                return {
                    "success": False,
                    "error": "Failed to parse generated topics"
                }
        else:
            return {
                "success": False,
                "error": "Failed to get valid response from Gemini"
            }
    
    except Exception as e:
        logging.error(f"Error during LinkedIn topic generation: {str(e)}")
        return {
            "success": False,
            "error": f"Topic generation error: {str(e)}"
        }

def generate_twitter_topics(analysis, count=5):
    """
    Generate Twitter post topics based on content analysis.
    
    Args:
        analysis (dict): Content analysis results
        count (int): Number of topics to generate
        
    Returns:
        dict: Dictionary containing Twitter topics
    """
    try:
        # Create Gemini model instance
        gemini_model = genai.GenerativeModel(model_name="gemini-1.5-pro", temperature=0.7)
        
        # Prepare the generation prompt
        prompt = f"""
        Based on this content analysis, generate {count} Twitter post topics.
        Each topic should:
        1. Be concise and engaging
        2. Focus on a single clear message
        3. Be suitable for a 280-character tweet
        4. Include a hook or attention-grabber
        5. Suggest 1-2 relevant hashtags
        
        Format each topic as a JSON object with:
        - title: The tweet's main message
        - description: Brief description of the angle
        - hashtags: 1-2 relevant hashtags
        
        Analysis:
        {json.dumps(analysis, indent=2)}
        """
        
        response = gemini_model.generate_content(prompt)
        
        if response and hasattr(response, 'text'):
            try:
                topics = json.loads(response.text)
                return {
                    "success": True,
                    "topics": topics
                }
            except json.JSONDecodeError:
                return {
                    "success": False,
                    "error": "Failed to parse generated topics"
                }
        else:
            return {
                "success": False,
                "error": "Failed to get valid response from Gemini"
            }
    
    except Exception as e:
        logging.error(f"Error during Twitter topic generation: {str(e)}")
        return {
            "success": False,
            "error": f"Topic generation error: {str(e)}"
        }

def generate_blog_post(topic, transcript, max_words=500):
    """
    Generate a blog post based on a topic and transcript.
    
    Args:
        topic (dict): The blog topic information
        transcript (str): The refined transcript text
        max_words (int): Maximum word count for the blog post
        
    Returns:
        dict: Dictionary containing the generated blog post
    """
    try:
        # Create Gemini model instance
        gemini_model = genai.GenerativeModel(model_name="gemini-1.5-pro", temperature=0.7)
        
        # Prepare the generation prompt
        prompt = f"""
        Create a blog post based on this topic and transcript.
        Topic details:
        {json.dumps(topic, indent=2)}
        
        Guidelines:
        1. Maximum {max_words} words
        2. Include a compelling headline
        3. Write an engaging introduction
        4. Cover the key points specified in the topic
        5. Include relevant quotes or examples from the transcript
        6. End with a clear conclusion and call-to-action
        
        Use this transcript as source material:
        {transcript[:3000]}  # Limit length to avoid token limits
        
        Format the blog post with clear headings and paragraphs.
        """
        
        response = gemini_model.generate_content(prompt)
        
        if response and hasattr(response, 'text'):
            blog_post = response.text.strip()
            word_count = len(blog_post.split())
            
            return {
                "success": True,
                "content": blog_post,
                "word_count": word_count,
                "topic": topic["title"]
            }
        else:
            return {
                "success": False,
                "error": "Failed to get valid response from Gemini"
            }
    
    except Exception as e:
        logging.error(f"Error during blog post generation: {str(e)}")
        return {
            "success": False,
            "error": f"Blog post generation error: {str(e)}"
        }

def generate_linkedin_post(topic, transcript, max_words=100):
    """
    Generate a LinkedIn post based on a topic and transcript.
    
    Args:
        topic (dict): The LinkedIn topic information
        transcript (str): The refined transcript text
        max_words (int): Maximum word count for the LinkedIn post
        
    Returns:
        dict: Dictionary containing the generated LinkedIn post
    """
    try:
        # Create Gemini model instance
        gemini_model = genai.GenerativeModel(model_name="gemini-1.5-pro", temperature=0.7)
        
        # Prepare the generation prompt
        prompt = f"""
        Create a LinkedIn post based on this topic and transcript.
        Topic details:
        {json.dumps(topic, indent=2)}
        
        Guidelines:
        1. Maximum {max_words} words
        2. Start with a strong hook
        3. Focus on professional insights
        4. Use short, impactful paragraphs
        5. Include relevant hashtags
        6. End with an engaging question or call-to-action
        
        Use this transcript as source material:
        {transcript[:2000]}  # Limit length to avoid token limits
        
        Format the post with appropriate line breaks and spacing.
        """
        
        response = gemini_model.generate_content(prompt)
        
        if response and hasattr(response, 'text'):
            linkedin_post = response.text.strip()
            word_count = len(linkedin_post.split())
            
            return {
                "success": True,
                "content": linkedin_post,
                "word_count": word_count,
                "topic": topic["title"]
            }
        else:
            return {
                "success": False,
                "error": "Failed to get valid response from Gemini"
            }
    
    except Exception as e:
        logging.error(f"Error during LinkedIn post generation: {str(e)}")
        return {
            "success": False,
            "error": f"LinkedIn post generation error: {str(e)}"
        }

def generate_twitter_post(topic, transcript, max_chars=280):
    """
    Generate a Twitter post based on a topic and transcript.
    
    Args:
        topic (dict): The Twitter topic information
        transcript (str): The refined transcript text
        max_chars (int): Maximum character count for the tweet
        
    Returns:
        dict: Dictionary containing the generated tweet
    """
    try:
        # Create Gemini model instance
        gemini_model = genai.GenerativeModel(model_name="gemini-1.5-pro", temperature=0.7)
        
        # Prepare the generation prompt
        prompt = f"""
        Create a tweet based on this topic and transcript.
        Topic details:
        {json.dumps(topic, indent=2)}
        
        Guidelines:
        1. Maximum {max_chars} characters
        2. Start with an attention-grabbing hook
        3. Focus on one clear message
        4. Include suggested hashtags
        5. Leave room for engagement
        
        Use this transcript as source material:
        {transcript[:1000]}  # Limit length to avoid token limits
        
        Ensure the tweet fits Twitter's character limit.
        """
        
        response = gemini_model.generate_content(prompt)
        
        if response and hasattr(response, 'text'):
            tweet = response.text.strip()
            char_count = len(tweet)
            
            # Truncate if over character limit
            if char_count > max_chars:
                tweet = tweet[:max_chars-3] + "..."
                char_count = len(tweet)
            
            return {
                "success": True,
                "content": tweet,
                "char_count": char_count,
                "topic": topic["title"]
            }
        else:
            return {
                "success": False,
                "error": "Failed to get valid response from Gemini"
            }
    
    except Exception as e:
        logging.error(f"Error during Twitter post generation: {str(e)}")
        return {
            "success": False,
            "error": f"Twitter post generation error: {str(e)}"
        }

def generate_all_content(transcript):
    """
    Generate all content types from a transcript.
    
    Args:
        transcript (str): The refined transcript text
        
    Returns:
        dict: Dictionary containing all generated content
    """
    try:
        # Step 1: Analyze transcript content
        analysis_result = analyze_transcript_content(transcript)
        if not analysis_result["success"]:
            return analysis_result
        
        analysis = analysis_result["analysis"]
        content = {"success": True}
        
        # Step 2: Generate topics for each platform
        # Blog topics
        blog_topics_result = generate_blog_topics(analysis)
        if blog_topics_result["success"]:
            content["blog_topics"] = blog_topics_result["topics"]
        
        # LinkedIn topics
        linkedin_topics_result = generate_linkedin_topics(analysis)
        if linkedin_topics_result["success"]:
            content["linkedin_topics"] = linkedin_topics_result["topics"]
        
        # Twitter topics
        twitter_topics_result = generate_twitter_topics(analysis)
        if twitter_topics_result["success"]:
            content["twitter_topics"] = twitter_topics_result["topics"]
        
        # Step 3: Generate content for each topic
        content["blog_posts"] = []
        content["linkedin_posts"] = []
        content["twitter_posts"] = []
        
        # Generate blog posts
        if "blog_topics" in content:
            for topic in content["blog_topics"]:
                result = generate_blog_post(topic, transcript)
                if result["success"]:
                    content["blog_posts"].append(result)
        
        # Generate LinkedIn posts
        if "linkedin_topics" in content:
            for topic in content["linkedin_topics"]:
                result = generate_linkedin_post(topic, transcript)
                if result["success"]:
                    content["linkedin_posts"].append(result)
        
        # Generate Twitter posts
        if "twitter_topics" in content:
            for topic in content["twitter_topics"]:
                result = generate_twitter_post(topic, transcript)
                if result["success"]:
                    content["twitter_posts"].append(result)
        
        return content
    
    except Exception as e:
        logging.error(f"Error during content generation: {str(e)}")
        return {
            "success": False,
            "error": f"Content generation error: {str(e)}"
        }

# Unit tests
def test_content_generation():
    """Test the content generation functions."""
    # Test transcript
    test_transcript = """
    In this video, we're discussing the future of artificial intelligence and its impact on various industries.
    The key points are:
    1. AI is transforming how we work
    2. Machine learning is becoming more accessible
    3. Companies need to adapt to AI-driven changes
    
    Let's explore each of these points in detail...
    """
    
    try:
        print("\nTesting content generation functions...")
        
        # Test content analysis
        analysis_result = analyze_transcript_content(test_transcript)
        assert analysis_result["success"] == True
        assert "analysis" in analysis_result
        print("✓ Content analysis passed")
        
        # Test topic generation
        topics_result = generate_blog_topics(analysis_result["analysis"])
        assert topics_result["success"] == True
        assert "topics" in topics_result
        print("✓ Topic generation passed")
        
        # Test blog post generation
        blog_result = generate_blog_post(topics_result["topics"][0], test_transcript)
        assert blog_result["success"] == True
        assert "content" in blog_result
        assert blog_result["word_count"] <= 500
        print("✓ Blog post generation passed")
        
        # Test LinkedIn post generation
        linkedin_result = generate_linkedin_post(topics_result["topics"][0], test_transcript)
        assert linkedin_result["success"] == True
        assert "content" in linkedin_result
        assert linkedin_result["word_count"] <= 100
        print("✓ LinkedIn post generation passed")
        
        # Test Twitter post generation
        twitter_result = generate_twitter_post(topics_result["topics"][0], test_transcript)
        assert twitter_result["success"] == True
        assert "content" in twitter_result
        assert twitter_result["char_count"] <= 280
        print("✓ Twitter post generation passed")
        
        # Test complete content generation
        all_content = generate_all_content(test_transcript)
        assert all_content["success"] == True
        assert "blog_posts" in all_content
        assert "linkedin_posts" in all_content
        assert "twitter_posts" in all_content
        print("✓ Complete content generation passed")
        
        print("\nAll content generation tests passed!")
        return True
    
    except AssertionError as e:
        print(f"Test failed: {str(e)}")
        return False
    except Exception as e:
        print(f"Error during testing: {str(e)}")
        return False

if __name__ == "__main__":
    # Run tests when module is executed directly
    test_content_generation()