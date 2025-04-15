import os
from dotenv import load_dotenv
import google.generativeai as genai

# Load environment variables
load_dotenv()

# Get API keys from environment variables
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
APIFY_API_KEY = os.getenv('APIFY_API_KEY')
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')

# Validate API keys
if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY is not set in the .env file.")
if not APIFY_API_KEY:
    raise ValueError("APIFY_API_KEY is not set in the .env file.")
if not OPENAI_API_KEY:
    raise ValueError("OPENAI_API_KEY is not set in the .env file.")

# Configure Gemini API
genai.configure(api_key=GEMINI_API_KEY)

def get_base_config():
    """
    Returns base configuration for AutoGen agents.
    """
    return {
        "config_list": [
            {
                "model": "gpt-4-turbo-preview",
                "api_key": OPENAI_API_KEY,
                "temperature": 0.7
            }
        ]
    }

def get_extraction_agent_config():
    """Configuration for the Extraction Agent"""
    config = get_base_config()
    config["config_list"][0]["temperature"] = 0.2
    
    # Store tool-specific configurations separately
    config["function_map"] = {
        "validate_youtube_url": None,  # Will be set in agent_setup.py
        "extract_youtube_transcript": None
    }
    
    return config

def get_refiner_agent_config():
    """Configuration for the Transcript Refiner Agent"""
    config = get_base_config()
    config["config_list"][0]["temperature"] = 0.3
    
    config["function_map"] = {
        "refine_transcript": None
    }
    
    return config

def get_topic_generator_config():
    """Configuration for the Topic Generator Agent"""
    config = get_base_config()
    config["config_list"][0]["temperature"] = 0.8
    
    config["function_map"] = {
        "generate_content_topics": None
    }
    
    return config

def get_writer_agent_config():
    """Configuration for the Writer Agents"""
    config = get_base_config()
    config["config_list"][0]["temperature"] = 0.7
    
    config["function_map"] = {
        "generate_blog_post": None,
        "generate_linkedin_post": None,
        "generate_twitter_post": None
    }
    
    return config

def get_editor_agent_config():
    """Configuration for the Editor Agents"""
    config = get_base_config()
    config["config_list"][0]["temperature"] = 0.2
    
    config["function_map"] = {
        "edit_blog_post": None,
        "edit_linkedin_post": None,
        "edit_twitter_post": None
    }
    
    return config

def get_group_chat_config():
    """Configuration for group chat management"""
    config = get_base_config()
    config["config_list"][0]["temperature"] = 0.5
    config.update({
        "max_round": 10,
        "human_input_mode": "NEVER"
    })
    return config

def get_gemini_config(model_name="gemini-1.5-pro", temperature=0.7):
    """Returns a config for using Gemini models."""
    return {
        "model": model_name,
        "api_key": GEMINI_API_KEY,
        "temperature": temperature,
        "safety_settings": [
            {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
            {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
            {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
            {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"}
        ]
    }

# Tool configurations (to be used by agents but not included in LLM config)
TOOL_CONFIGS = {
    "extraction": {
        "apify_api_key": APIFY_API_KEY,
        "max_retries": 5,
        "timeout": 600
    },
    "content_limits": {
        "blog": 500,      # words
        "linkedin": 100,  # words
        "twitter": 280   # characters
    },
    "timeouts": {
        "extraction": 600,   # 10 minutes
        "refinement": 300,   # 5 minutes
        "generation": 300,   # 5 minutes
        "editing": 300      # 5 minutes
    }
}