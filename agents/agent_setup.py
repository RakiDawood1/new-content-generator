import os
import json
import logging
from autogen import AssistantAgent, UserProxyAgent, GroupChat, GroupChatManager
from .agent_config import (
    get_extraction_agent_config,
    get_refiner_agent_config,
    get_topic_generator_config,
    get_writer_agent_config, 
    get_editor_agent_config,
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
        # User Proxy Agent - Central coordinator
        self.agents["user_proxy"] = UserProxyAgent(
            name="UserProxy",
            system_message=USER_PROXY_PROMPT,
            human_input_mode="NEVER",
            max_consecutive_auto_reply=10,
            code_execution_config=False,  # Disable code execution for safety
            llm_config=get_group_chat_config()
        )
        
        # Create function map with tool configurations
        function_map = {
            "validate_youtube_url": validate_youtube_url,
            "extract_youtube_transcript": lambda url: extract_youtube_transcript(url, TOOL_CONFIGS["extraction"]),
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
        
        # Extraction Agent
        extraction_config = get_extraction_agent_config()
        extraction_config["function_map"] = {
            k: function_map[k] for k in ["validate_youtube_url", "extract_youtube_transcript"]
        }
        self.agents["extraction"] = AssistantAgent(
            name="ExtractionAgent",
            system_message=EXTRACTION_AGENT_PROMPT,
            llm_config=extraction_config
        )
        
        # Transcript Refiner Agent
        refiner_config = get_refiner_agent_config()
        refiner_config["function_map"] = {"refine_transcript": function_map["refine_transcript"]}
        self.agents["refiner"] = AssistantAgent(
            name="TranscriptRefinerAgent",
            system_message=TRANSCRIPT_REFINER_PROMPT,
            llm_config=refiner_config
        )
        
        # Topic Generator Agent
        topic_gen_config = get_topic_generator_config()
        topic_gen_config["function_map"] = {"generate_content_topics": function_map["generate_content_topics"]}
        self.agents["topic_generator"] = AssistantAgent(
            name="TopicGeneratorAgent",
            system_message=TOPIC_GENERATOR_PROMPT,
            llm_config=topic_gen_config
        )
        
        # Content Writer Agents
        writer_config = get_writer_agent_config()
        self.agents["blog_writer"] = AssistantAgent(
            name="BlogWriterAgent",
            system_message=BLOG_WRITER_PROMPT,
            llm_config=writer_config
        )
        
        self.agents["linkedin_writer"] = AssistantAgent(
            name="LinkedInWriterAgent",
            system_message=LINKEDIN_WRITER_PROMPT,
            llm_config=writer_config
        )
        
        self.agents["twitter_writer"] = AssistantAgent(
            name="TwitterWriterAgent",
            system_message=TWITTER_WRITER_PROMPT,
            llm_config=writer_config
        )
        
        # Content Editor Agents
        editor_config = get_editor_agent_config()
        self.agents["blog_editor"] = AssistantAgent(
            name="BlogEditorAgent",
            system_message=BLOG_EDITOR_PROMPT,
            llm_config=editor_config
        )
        
        self.agents["linkedin_editor"] = AssistantAgent(
            name="LinkedInEditorAgent",
            system_message=LINKEDIN_EDITOR_PROMPT,
            llm_config=editor_config
        )
        
        self.agents["twitter_editor"] = AssistantAgent(
            name="TwitterEditorAgent",
            system_message=TWITTER_EDITOR_PROMPT,
            llm_config=editor_config
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
            result = self.agents["extraction"].run_function(
                function_name="extract_youtube_transcript",
                arguments={"url": youtube_url}
            )
            
            if not result["success"]:
                return result
            
            self.content_data["video_info"] = result["video_info"]
            self.content_data["transcript"] = result["transcript"]
            
            # Step 2: Refine transcript
            logging.info("Step 2: Refining the transcript")
            result = self.agents["refiner"].run_function(
                function_name="refine_transcript",
                arguments={"transcript": self.content_data["transcript"]}
            )
            
            if not result["success"]:
                return result
            
            self.content_data["refined_transcript"] = result["refined_transcript"]
            
            # Step 3: Generate topics
            logging.info("Step 3: Generating content topics")
            result = self.agents["topic_generator"].run_function(
                function_name="generate_content_topics",
                arguments={"transcript": self.content_data["refined_transcript"]}
            )
            
            if not result["success"]:
                return result
            
            self.content_data["topics"] = result["topics"]
            
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
        
        platform_topics = self.content_data["topics"].get(f"{platform}_topics", [])
        writer_agent = self.agents[f"{platform}_writer"]
        editor_agent = self.agents[f"{platform}_editor"]
        
        for topic in platform_topics:
            # Generate content
            generation_func = f"generate_{platform}_post"
            result = writer_agent.run_function(
                function_name=generation_func,
                arguments={
                    "topic": topic,
                    "transcript": self.content_data["refined_transcript"]
                }
            )
            
            if not result["success"]:
                logging.warning(f"Failed to generate {platform} content for topic: {topic.get('title', 'Unknown')}")
                continue
            
            # Edit content
            edit_func = f"edit_{platform}_post"
            edit_result = editor_agent.run_function(
                function_name=edit_func,
                arguments={"content": result["content"]}
            )
            
            if not edit_result["success"]:
                logging.warning(f"Failed to edit {platform} content for topic: {topic.get('title', 'Unknown')}")
                edit_result = result
            
            # Store the content
            self.content_data[f"{platform}_posts"].append(edit_result)