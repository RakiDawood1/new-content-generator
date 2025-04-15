import os
from dotenv import load_dotenv
import google.generativeai as genai
from autogen import config_list_from_json

# Load environment variables
load_dotenv()

# Get API key from environment variables
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
APIFY_API_KEY = os.getenv('APIFY_API_KEY')

# Configure Gemini API
genai.configure(api_key=GEMINI_API_KEY)

# Define function to get the configuration for AutoGen agents using Gemini
def get_gemini_config(model_name="gemini-1.5-pro", temperature=0.7, max_tokens=2048):
    """
    Returns a config for AutoGen to use with Gemini models.
    
    Args:
        model_name (str): The Gemini model to use
        temperature (float): The temperature for generation (0.0 to 1.0)
        max_tokens (int): Maximum tokens to generate
        
    Returns:
        dict: Configuration dict for AutoGen
    """
    if not GEMINI_API_KEY:
        raise ValueError("GEMINI_API_KEY is not set in the .env file.")
    
    config = {
        "model": model_name,
        "api_key": GEMINI_API_KEY,
        "temperature": temperature,
        "max_tokens": max_tokens
    }
    
    return config

# Create config list function for AutoGen
def get_gemini_config_list(models=None):
    """
    Creates a configuration list for AutoGen with Gemini models.
    
    Args:
        models (list): List of model configurations to use
        
    Returns:
        list: List of configurations for AutoGen
    """
    if models is None:
        models = [
            {"model": "gemini-1.5-pro", "temperature": 0.7, "max_tokens": 2048}
        ]
    
    config_list = []
    for model_config in models:
        config = get_gemini_config(
            model_name=model_config.get("model", "gemini-1.5-pro"),
            temperature=model_config.get("temperature", 0.7),
            max_tokens=model_config.get("max_tokens", 2048)
        )
        config_list.append(config)
    
    return config_list

# Agent-specific configurations
def get_extraction_agent_config():
    """Configuration for the Extraction Agent - lower temperature for more precise output"""
    return get_gemini_config(temperature=0.2, max_tokens=4096)

def get_refiner_agent_config():
    """Configuration for the Transcript Refiner Agent - balanced temperature"""
    return get_gemini_config(temperature=0.3, max_tokens=8192)

def get_topic_generator_config():
    """Configuration for the Topic Generator Agent - higher temperature for creativity"""
    return get_gemini_config(temperature=0.8, max_tokens=4096)

def get_writer_agent_config():
    """Configuration for the Writer Agents - high temperature for creative content"""
    return get_gemini_config(temperature=0.7, max_tokens=4096)

def get_editor_agent_config():
    """Configuration for the Editor Agents - low temperature for precise edits"""
    return get_gemini_config(temperature=0.2, max_tokens=4096)