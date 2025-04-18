"""
Updated agent_setup.py with fixed agent initialization
to address Pydantic validation errors in AutoGen.
"""

import os
import json
import logging
from autogen import AssistantAgent, UserProxyAgent, GroupChat, GroupChatManager
from .agent_config import (
    get_base_config,
    get_extraction_agent_config, 
    get_refiner_agent_config,
    get_topic_generator_config,
    get_writer_agent_config, 
    get_editor_agent_config,
    get_user_proxy_config,
    get_group_chat_config,
    TOOL_CONFIGS
)
from .agent_prompts import (
    EXTRACTION_AGENT_PROMPT,
    TRANSCRIPT_REFINER_PROMPT,
    TOPIC_GENERATOR_PROMPT,
    BLOG_WRITER_PROMPT,
    LINKEDIN_WRITER_PROMPT,
    TWITTER_WRITER_PROMPT,
    BLOG_EDITOR_PROMPT,
    LINKEDIN_EDITOR_PROMPT,
    TWITTER_EDITOR_PROMPT,
    USER_PROXY_PROMPT
)
from .agent_tools import *  # Import all tools

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class RepurposerAgentSystem:
    """Main class for setting up and orchestrating the Content Repurposer agent system."""
    
    def __init__(self):
        """Initialize the agent system."""
        self.agents = {}
        self.group_chats = {}
        self.content_data = {
            "video_url": None,
            "video_info": None,
            "transcript": None,
            "refined_transcript": None,
            "topics": None,
            "blog_posts": [],
            "linkedin_posts": [],
            "twitter_posts": []
        }
        
        # Set up agents
        self._setup_agents()
    
    def _setup_agents(self):
        """Set up all agents in the system."""
        # Create function map for tools
        function_map = {
            "validate_youtube_url": validate_youtube_url,
            "extract_youtube_transcript": lambda url: extract_youtube_transcript(url),
            "refine_transcript": refine_transcript,
            "generate_content_topics": generate_content_topics,
            "generate_blog_post": lambda topic, transcript: generate_blog_post(
                topic, transcript, TOOL_CONFIGS["content_limits"]["blog"]
            ),
            "generate_linkedin_post": lambda topic, transcript: generate_linkedin_post(
                topic, transcript, TOOL_CONFIGS["content_limits"]["linkedin"]
            ),
            "generate_twitter_post": lambda topic, transcript: generate_twitter_post(
                topic, transcript, TOOL_CONFIGS["content_limits"]["twitter"]
            ),
            "edit_blog_post": edit_blog_post,
            "edit_linkedin_post": edit_linkedin_post,
            "edit_twitter_post": edit_twitter_post,
            "save_output": save_output
        }
        
        # User Proxy Agent - Central coordinator
        user_proxy_config = get_user_proxy_config()
        self.agents["user_proxy"] = UserProxyAgent(
            name="UserProxy",
            system_message=USER_PROXY_PROMPT,
            human_input_mode=user_proxy_config["human_input_mode"],
            max_consecutive_auto_reply=10,
            code_execution_config={"last_n_messages": 1, "work_dir": "temp", "use_docker": False},
            llm_config=get_base_config()  # Only pass the base config
        )
        
        # Extraction Agent
        extraction_config = get_extraction_agent_config()
        self.agents["extraction"] = AssistantAgent(
            name="ExtractionAgent",
            system_message=EXTRACTION_AGENT_PROMPT,
            llm_config=extraction_config
        )
        # Add function map separately
        self.agents["extraction"].register_function(
            function_map={"validate_youtube_url": function_map["validate_youtube_url"],
                        "extract_youtube_transcript": function_map["extract_youtube_transcript"]}
        )
        
        # Transcript Refiner Agent
        refiner_config = get_refiner_agent_config()
        self.agents["refiner"] = AssistantAgent(
            name="TranscriptRefinerAgent",
            system_message=TRANSCRIPT_REFINER_PROMPT,
            llm_config=refiner_config
        )
        # Add function map separately
        self.agents["refiner"].register_function(
            function_map={"refine_transcript": function_map["refine_transcript"]}
        )
        
        # Topic Generator Agent
        topic_gen_config = get_topic_generator_config()
        self.agents["topic_generator"] = AssistantAgent(
            name="TopicGeneratorAgent",
            system_message=TOPIC_GENERATOR_PROMPT,
            llm_config=topic_gen_config
        )
        # Add function map separately
        self.agents["topic_generator"].register_function(
            function_map={"generate_content_topics": function_map["generate_content_topics"]}
        )
        
        # Content Writer Agents
        writer_config = get_writer_agent_config()
        self.agents["blog_writer"] = AssistantAgent(
            name="BlogWriterAgent",
            system_message=BLOG_WRITER_PROMPT,
            llm_config=writer_config
        )
        # Add function map separately
        self.agents["blog_writer"].register_function(
            function_map={"generate_blog_post": function_map["generate_blog_post"]}
        )
        
        self.agents["linkedin_writer"] = AssistantAgent(
            name="LinkedInWriterAgent",
            system_message=LINKEDIN_WRITER_PROMPT,
            llm_config=writer_config
        )
        # Add function map separately
        self.agents["linkedin_writer"].register_function(
            function_map={"generate_linkedin_post": function_map["generate_linkedin_post"]}
        )
        
        self.agents["twitter_writer"] = AssistantAgent(
            name="TwitterWriterAgent",
            system_message=TWITTER_WRITER_PROMPT,
            llm_config=writer_config
        )
        # Add function map separately
        self.agents["twitter_writer"].register_function(
            function_map={"generate_twitter_post": function_map["generate_twitter_post"]}
        )
        
        # Content Editor Agents
        editor_config = get_editor_agent_config()
        self.agents["blog_editor"] = AssistantAgent(
            name="BlogEditorAgent",
            system_message=BLOG_EDITOR_PROMPT,
            llm_config=editor_config
        )
        # Add function map separately
        self.agents["blog_editor"].register_function(
            function_map={"edit_blog_post": function_map["edit_blog_post"]}
        )
        
        self.agents["linkedin_editor"] = AssistantAgent(
            name="LinkedInEditorAgent",
            system_message=LINKEDIN_EDITOR_PROMPT,
            llm_config=editor_config
        )
        # Add function map separately
        self.agents["linkedin_editor"].register_function(
            function_map={"edit_linkedin_post": function_map["edit_linkedin_post"]}
        )
        
        self.agents["twitter_editor"] = AssistantAgent(
            name="TwitterEditorAgent",
            system_message=TWITTER_EDITOR_PROMPT,
            llm_config=editor_config
        )
        # Add function map separately
        self.agents["twitter_editor"].register_function(
            function_map={"edit_twitter_post": function_map["edit_twitter_post"]}
        )
    
    def process_youtube_url(self, youtube_url):
        """
        Process a YouTube URL through the complete pipeline.
        
        Args:
            youtube_url (str): The YouTube URL to process
            
        Returns:
            dict: The final content data with all generated content
        """
        try:
            # Store the URL
            self.content_data["video_url"] = youtube_url
            
            # Step 1: Extract transcript
            logging.info("Step 1: Extracting transcript from YouTube URL")
            extraction_agent = self.agents["extraction"]
            
            # Call function directly to avoid relying on chat
            validation = validate_youtube_url(youtube_url)
            if not validation["valid"]:
                return {"success": False, "error": validation["error"]}
                
            extraction_result = extract_youtube_transcript(youtube_url)

            # Log the result received from extraction
            logging.warning(f"Received extraction_result: {json.dumps(extraction_result, indent=2)}")
            
            if not extraction_result["success"]:
                logging.error(f"Extraction failed. Result: {extraction_result.get('error')}")
                return extraction_result
            
            self.content_data["video_info"] = extraction_result["video_info"]
            self.content_data["transcript"] = extraction_result["transcript"]
            
            # Log the transcript being passed to refinement
            logging.warning(f"Transcript passed to refinement (first 500 chars): '{self.content_data['transcript'][:500]}'")
            
            # Step 2: Refine transcript
            logging.info("Step 2: Refining the transcript")
            refinement_result = refine_transcript(self.content_data["transcript"])
            
            if not refinement_result["success"]:
                return refinement_result
            
            self.content_data["refined_transcript"] = refinement_result["refined_transcript"]
            
            # Step 3: Generate topics
            logging.info("Step 3: Generating content topics")
            topic_result = generate_content_topics(self.content_data["refined_transcript"])
            
            if not topic_result["success"]:
                return topic_result
            
            self.content_data["topics"] = topic_result["topics"]
            
            # Step 4: Generate and edit content for each platform
            for platform in ["blog", "linkedin", "twitter"]:
                self._generate_platform_content(platform)
            
            # Step 5: Save all content
            output_result = save_output(self.content_data)
            
            if not output_result["success"]:
                return output_result
            
            return {
                "success": True,
                "content_data": self.content_data,
                "output_file": output_result["file_path"]
            }
        
        except Exception as e:
            logging.error(f"Error in process_youtube_url: {str(e)}")
            return {
                "success": False,
                "error": f"Processing error: {str(e)}"
            }
    
    def _generate_platform_content(self, platform):
        """Generate content for a specific platform."""
        logging.info(f"Generating {platform} content")
        
        # Use all topics for each platform since we're not separating them by platform anymore
        for topic in self.content_data["topics"]:
            # Generate content
            generation_func = f"generate_{platform}_post"
            
            # Call the appropriate function directly
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
            edit_func = f"edit_{platform}_post"
            
            # Call the appropriate editing function directly
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