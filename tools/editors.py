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

def check_content_quality(content, content_type):
    """
    Check content for quality issues and platform appropriateness.
    
    Args:
        content (str): The content to check
        content_type (str): Type of content ('blog', 'linkedin', or 'twitter')
        
    Returns:
        dict: Dictionary containing quality check results
    """
    try:
        # Create Gemini model instance
        gemini_model = genai.GenerativeModel(model_name="gemini-1.5-pro", temperature=0.2)
        
        # Prepare platform-specific criteria
        platform_criteria = {
            'blog': {
                'max_length': 500,  # words
                'structure': ['headline', 'introduction', 'body', 'conclusion'],
                'style': 'informative and engaging'
            },
            'linkedin': {
                'max_length': 100,  # words
                'structure': ['hook', 'insight', 'call-to-action'],
                'style': 'professional and insightful'
            },
            'twitter': {
                'max_length': 280,  # characters
                'structure': ['hook', 'message', 'hashtags'],
                'style': 'concise and engaging'
            }
        }
        
        if content_type not in platform_criteria:
            return {
                "success": False,
                "error": f"Invalid content type: {content_type}"
            }
        
        criteria = platform_criteria[content_type]
        
        # Prepare the analysis prompt
        prompt = f"""
        Analyze this {content_type} content for quality and platform appropriateness.
        Check for:
        1. Length (max: {criteria['max_length']} {'words' if content_type != 'twitter' else 'characters'})
        2. Structure (expected: {', '.join(criteria['structure'])})
        3. Style (should be {criteria['style']})
        4. Grammar and clarity
        5. Platform suitability
        
        Content:
        {content}
        
        Return analysis as JSON with these keys:
        - length_check: boolean (within limit?)
        - structure_check: boolean (has required elements?)
        - style_check: boolean (appropriate style?)
        - grammar_check: boolean (grammatically correct?)
        - platform_check: boolean (suitable for platform?)
        - issues: list of specific issues found
        - suggestions: list of improvement suggestions
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
                    "error": "Failed to parse quality analysis results"
                }
        else:
            return {
                "success": False,
                "error": "Failed to get valid response from Gemini"
            }
    
    except Exception as e:
        logging.error(f"Error during content quality check: {str(e)}")
        return {
            "success": False,
            "error": f"Quality check error: {str(e)}"
        }

def edit_blog_post(blog_post):
    """
    Edit and improve a blog post.
    
    Args:
        blog_post (dict): The blog post content and metadata
        
    Returns:
        dict: Dictionary containing the edited blog post
    """
    try:
        if not blog_post or "content" not in blog_post:
            return {
                "success": False,
                "error": "Invalid blog post data"
            }
        
        # First check quality
        quality_result = check_content_quality(blog_post["content"], "blog")
        if not quality_result["success"]:
            return quality_result
        
        # Create Gemini model instance
        gemini_model = genai.GenerativeModel(model_name="gemini-1.5-pro", temperature=0.3)
        
        # Prepare the editing prompt
        prompt = f"""
        Edit and improve this blog post while maintaining its core message.
        
        Original post:
        {blog_post["content"]}
        
        Quality analysis:
        {json.dumps(quality_result["analysis"], indent=2)}
        
        Guidelines:
        1. Address identified issues
        2. Ensure clear structure (headline, intro, body, conclusion)
        3. Maintain professional but engaging tone
        4. Keep within 500-word limit
        5. Improve clarity and flow
        6. Fix any grammar or style issues
        
        Return only the edited blog post, maintaining formatting.
        """
        
        response = gemini_model.generate_content(prompt)
        
        if response and hasattr(response, 'text'):
            edited_content = response.text.strip()
            word_count = len(edited_content.split())
            
            return {
                "success": True,
                "original_content": blog_post["content"],
                "edited_content": edited_content,
                "word_count": word_count,
                "quality_analysis": quality_result["analysis"]
            }
        else:
            return {
                "success": False,
                "error": "Failed to get valid response from Gemini"
            }
    
    except Exception as e:
        logging.error(f"Error during blog post editing: {str(e)}")
        return {
            "success": False,
            "error": f"Blog post editing error: {str(e)}"
        }

def edit_linkedin_post(linkedin_post):
    """
    Edit and improve a LinkedIn post.
    
    Args:
        linkedin_post (dict): The LinkedIn post content and metadata
        
    Returns:
        dict: Dictionary containing the edited LinkedIn post
    """
    try:
        if not linkedin_post or "content" not in linkedin_post:
            return {
                "success": False,
                "error": "Invalid LinkedIn post data"
            }
        
        # First check quality
        quality_result = check_content_quality(linkedin_post["content"], "linkedin")
        if not quality_result["success"]:
            return quality_result
        
        # Create Gemini model instance
        gemini_model = genai.GenerativeModel(model_name="gemini-1.5-pro", temperature=0.3)
        
        # Prepare the editing prompt
        prompt = f"""
        Edit and improve this LinkedIn post while maintaining its core message.
        
        Original post:
        {linkedin_post["content"]}
        
        Quality analysis:
        {json.dumps(quality_result["analysis"], indent=2)}
        
        Guidelines:
        1. Address identified issues
        2. Ensure strong hook and clear call-to-action
        3. Maintain professional tone
        4. Keep within 100-word limit
        5. Format with appropriate line breaks
        6. Verify hashtag relevance and formatting
        
        Return only the edited LinkedIn post, maintaining formatting.
        """
        
        response = gemini_model.generate_content(prompt)
        
        if response and hasattr(response, 'text'):
            edited_content = response.text.strip()
            word_count = len(edited_content.split())
            
            return {
                "success": True,
                "original_content": linkedin_post["content"],
                "edited_content": edited_content,
                "word_count": word_count,
                "quality_analysis": quality_result["analysis"]
            }
        else:
            return {
                "success": False,
                "error": "Failed to get valid response from Gemini"
            }
    
    except Exception as e:
        logging.error(f"Error during LinkedIn post editing: {str(e)}")
        return {
            "success": False,
            "error": f"LinkedIn post editing error: {str(e)}"
        }

def edit_twitter_post(twitter_post):
    """
    Edit and improve a Twitter post.
    
    Args:
        twitter_post (dict): The Twitter post content and metadata
        
    Returns:
        dict: Dictionary containing the edited tweet
    """
    try:
        if not twitter_post or "content" not in twitter_post:
            return {
                "success": False,
                "error": "Invalid Twitter post data"
            }
        
        # First check quality
        quality_result = check_content_quality(twitter_post["content"], "twitter")
        if not quality_result["success"]:
            return quality_result
        
        # Create Gemini model instance
        gemini_model = genai.GenerativeModel(model_name="gemini-1.5-pro", temperature=0.3)
        
        # Prepare the editing prompt
        prompt = f"""
        Edit and improve this tweet while maintaining its core message.
        
        Original tweet:
        {twitter_post["content"]}
        
        Quality analysis:
        {json.dumps(quality_result["analysis"], indent=2)}
        
        Guidelines:
        1. Address identified issues
        2. Ensure strong hook and clear message
        3. Keep within 280-character limit
        4. Verify hashtag relevance
        5. Maximize engagement potential
        6. Leave room for replies/comments
        
        Return only the edited tweet, no additional text.
        """
        
        response = gemini_model.generate_content(prompt)
        
        if response and hasattr(response, 'text'):
            edited_content = response.text.strip()
            char_count = len(edited_content)
            
            # Ensure tweet doesn't exceed character limit
            if char_count > 280:
                edited_content = edited_content[:277] + "..."
                char_count = len(edited_content)
            
            return {
                "success": True,
                "original_content": twitter_post["content"],
                "edited_content": edited_content,
                "char_count": char_count,
                "quality_analysis": quality_result["analysis"]
            }
        else:
            return {
                "success": False,
                "error": "Failed to get valid response from Gemini"
            }
    
    except Exception as e:
        logging.error(f"Error during Twitter post editing: {str(e)}")
        return {
            "success": False,
            "error": f"Twitter post editing error: {str(e)}"
        }

def edit_all_content(content_data):
    """
    Edit all generated content.
    
    Args:
        content_data (dict): Dictionary containing all generated content
        
    Returns:
        dict: Dictionary containing all edited content
    """
    try:
        edited_content = {"success": True}
        
        # Edit blog posts
        if "blog_posts" in content_data:
            edited_content["blog_posts"] = []
            for post in content_data["blog_posts"]:
                result = edit_blog_post(post)
                if result["success"]:
                    edited_content["blog_posts"].append(result)
                else:
                    logging.warning(f"Failed to edit blog post: {result.get('error', 'Unknown error')}")
        
        # Edit LinkedIn posts
        if "linkedin_posts" in content_data:
            edited_content["linkedin_posts"] = []
            for post in content_data["linkedin_posts"]:
                result = edit_linkedin_post(post)
                if result["success"]:
                    edited_content["linkedin_posts"].append(result)
                else:
                    logging.warning(f"Failed to edit LinkedIn post: {result.get('error', 'Unknown error')}")
        
        # Edit Twitter posts
        if "twitter_posts" in content_data:
            edited_content["twitter_posts"] = []
            for post in content_data["twitter_posts"]:
                result = edit_twitter_post(post)
                if result["success"]:
                    edited_content["twitter_posts"].append(result)
                else:
                    logging.warning(f"Failed to edit Twitter post: {result.get('error', 'Unknown error')}")
        
        return edited_content
    
    except Exception as e:
        logging.error(f"Error during content editing: {str(e)}")
        return {
            "success": False,
            "error": f"Content editing error: {str(e)}"
        }

# Unit tests
def test_content_editing():
    """Test the content editing functions."""
    # Test content
    test_blog_post = {
        "content": """
        The Future of AI in Business
        
        Artificial Intelligence is transforming how businesses operate. Companies need to adapt
        to these changes to remain competitive in the modern marketplace.
        
        Key points:
        1. AI automation is increasing productivity
        2. Machine learning is improving decision-making
        3. Companies must invest in AI technology
        
        In conclusion, AI adoption is crucial for business success.
        """
    }
    
    test_linkedin_post = {
        "content": """
        🤖 AI is revolutionizing business operations! Here's what you need to know:
        
        We're seeing unprecedented growth in AI adoption across industries. The key is understanding
        how to leverage this technology effectively.
        
        What's your take on AI in business?
        
        #AI #BusinessInnovation #FutureOfWork
        """
    }
    
    test_twitter_post = {
        "content": """
        🚀 AI is reshaping how we do business! Companies that adapt will thrive, while others fall behind.
        
        What's your AI strategy?
        
        #AI #Innovation
        """
    }
    
    try:
        print("\nTesting content editing functions...")
        
        # Test quality checking
        quality_result = check_content_quality(test_blog_post["content"], "blog")
        assert quality_result["success"] == True
        assert "analysis" in quality_result
        print("✓ Content quality checking passed")
        
        # Test blog post editing
        blog_result = edit_blog_post(test_blog_post)
        assert blog_result["success"] == True
        assert "edited_content" in blog_result
        assert blog_result["word_count"] <= 500
        print("✓ Blog post editing passed")
        
        # Test LinkedIn post editing
        linkedin_result = edit_linkedin_post(test_linkedin_post)
        assert linkedin_result["success"] == True
        assert "edited_content" in linkedin_result
        assert linkedin_result["word_count"] <= 100
        print("✓ LinkedIn post editing passed")
        
        # Test Twitter post editing
        twitter_result = edit_twitter_post(test_twitter_post)
        assert twitter_result["success"] == True
        assert "edited_content" in twitter_result
        assert twitter_result["char_count"] <= 280
        print("✓ Twitter post editing passed")
        
        # Test complete content editing
        test_content_data = {
            "blog_posts": [test_blog_post],
            "linkedin_posts": [test_linkedin_post],
            "twitter_posts": [test_twitter_post]
        }
        
        all_edited = edit_all_content(test_content_data)
        assert all_edited["success"] == True
        assert "blog_posts" in all_edited
        assert "linkedin_posts" in all_edited
        assert "twitter_posts" in all_edited
        print("✓ Complete content editing passed")
        
        print("\nAll content editing tests passed!")
        return True
    
    except AssertionError as e:
        print(f"Test failed: {str(e)}")
        return False
    except Exception as e:
        print(f"Error during testing: {str(e)}")
        return False

if __name__ == "__main__":
    # Run tests when module is executed directly
    test_content_editing()