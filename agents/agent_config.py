"""
Updated agent_config.py with fixed AutoGen configuration
to address Pydantic validation errors.
"""

import os
import logging
from dotenv import load_dotenv
import google.generativeai as genai
from openai import OpenAI

# Load environment variables
load_dotenv()

# Get API keys from environment variables
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
APIFY_API_KEY = os.getenv('APIFY_API_KEY')
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
DEEPSEEK_API_KEY = os.getenv('DEEPSEEK_API_KEY')

# Validate API keys
if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY is not set in the .env file.")
if not APIFY_API_KEY:
    raise ValueError("APIFY_API_KEY is not set in the .env file.")
if not OPENAI_API_KEY:
    raise ValueError("OPENAI_API_KEY is not set in the .env file.")
if not DEEPSEEK_API_KEY:
    raise ValueError("DEEPSEEK_API_KEY is not set in the .env file.")

# Configure Gemini API
genai.configure(api_key=GEMINI_API_KEY)

# Initialize DeepSeek client
client = OpenAI(
    api_key=DEEPSEEK_API_KEY,
    base_url="https://api.deepseek.com/v1"
)

def get_base_config():
    """
    Returns base configuration for AutoGen agents.
    
    Fixed to use the correct format expected by AutoGen v0.2+
    """
    return {
        "config_list": [
            {
                "model": "gpt-3.5-turbo",
                "api_key": OPENAI_API_KEY
            }
        ]
    }

def get_extraction_agent_config():
    """Configuration for the Extraction Agent"""
    config = get_base_config()
    
    # Function map will be set separately to avoid validation errors
    return config

def get_refiner_agent_config():
    """Configuration for the Transcript Refiner Agent"""
    config = get_base_config()
    
    # Function map will be set separately to avoid validation errors
    return config

def get_topic_generator_config():
    """Configuration for the Topic Generator Agent"""
    config = get_base_config()
    
    # Function map will be set separately to avoid validation errors
    return config

def get_writer_agent_config():
    """Configuration for the Writer Agents"""
    config = get_base_config()
    
    # Function map will be set separately to avoid validation errors
    return config

def get_editor_agent_config():
    """Configuration for the Editor Agents"""
    config = get_base_config()
    
    # Function map will be set separately to avoid validation errors
    return config

def get_user_proxy_config():
    """Configuration for user proxy agent"""
    return {
        "human_input_mode": "NEVER",
    }

def get_group_chat_config():
    """Configuration for group chat management"""
    return {
        "llm_config": get_base_config(),
    }

def get_deepseek_config(temperature=0.7):
    """Returns a config for using DeepSeek models."""
    return {
        "api_key": DEEPSEEK_API_KEY,
        "model": "deepseek-chat",
        "temperature": temperature,
        "max_tokens": 2048
    }

def get_apify_config():
    """Returns a config for using Apify."""
    return {
        "api_key": APIFY_API_KEY,
        "actor_id": "1s7eXiaukVuOr4Ueg",  # YouTube transcript extractor
        "memory_mbytes": 4096
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

# Logging configuration
logging_config = {
    "level": logging.INFO,
    "format": '%(asctime)s - %(levelname)s - %(message)s'
}

# Content generation settings
content_config = {
    "max_blog_words": 500,
    "max_linkedin_words": 100,
    "max_twitter_chars": 280,
    "posts_per_platform": {
        "blog": 1,
        "linkedin": 2,
        "twitter": 5
    },
    "delay_between_calls": 3  # Seconds between API calls
}

# Output settings
output_config = {
    "output_dir": "output",
    "output_file": "repurposed_content.txt"
}