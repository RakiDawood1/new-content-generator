import os
import json
import logging
from autogen import AssistantAgent, UserProxyAgent, GroupChat, GroupChatManager
from .agent_config import (
    get_extraction_agent_config,
    get_refiner_agent_config,
    get_topic_generator_config,
    get_writer_agent_config, 
    get_editor_agent_config
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
from .agent_tools import (
    validate_youtube_url,
    extract_youtube_transcript,
    refine_transcript,
    generate_content_topics,
    generate_blog_post,
    generate_linkedin_post,
    generate_twitter_post,
    edit_blog_post,
    edit_linkedin_post,
    edit_twitter_post,
    save_output
)

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class RepurposerAgentSystem:
    """
    Main class for setting up and orchestrating the Content Repurposer agent system.
    """
    
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
            is_termination_msg=lambda x: x.get("content", "") and "TASK_COMPLETE" in x.get("content", ""),
            code_execution_config={
                "last_n_messages": 3,
                "work_dir": "workspace",
                "use_docker": False
            },
            function_map={
                "validate_youtube_url": validate_youtube_url,
                "extract_youtube_transcript": extract_youtube_transcript,
                "refine_transcript": refine_transcript,
                "generate_content_topics": generate_content_topics,
                "generate_blog_post": generate_blog_post,
                "generate_linkedin_post": generate_linkedin_post,
                "generate_twitter_post": generate_twitter_post,
                "edit_blog_post": edit_blog_post,
                "edit_linkedin_post": edit_linkedin_post,
                "edit_twitter_post": edit_twitter_post,
                "save_output": save_output
            }
        )
        
        # Extraction Agent
        self.agents["extraction"] = AssistantAgent(
            name="ExtractionAgent",
            system_message=EXTRACTION_AGENT_PROMPT,
            llm_config=get_extraction_agent_config()
        )
        
        # Transcript Refiner Agent
        self.agents["refiner"] = AssistantAgent(
            name="TranscriptRefinerAgent",
            system_message=TRANSCRIPT_REFINER_PROMPT,
            llm_config=get_refiner_agent_config()
        )
        
        # Topic Generator Agent
        self.agents["topic_generator"] = AssistantAgent(
            name="TopicGeneratorAgent",
            system_message=TOPIC_GENERATOR_PROMPT,
            llm_config=get_topic_generator_config()
        )
        
        # Content Writer Agents
        self.agents["blog_writer"] = AssistantAgent(
            name="BlogWriterAgent",
            system_message=BLOG_WRITER_PROMPT,
            llm_config=get_writer_agent_config()
        )
        
        self.agents["linkedin_writer"] = AssistantAgent(
            name="LinkedInWriterAgent",
            system_message=LINKEDIN_WRITER_PROMPT,
            llm_config=get_writer_agent_config()
        )
        
        self.agents["twitter_writer"] = AssistantAgent(
            name="TwitterWriterAgent",
            system_message=TWITTER_WRITER_PROMPT,
            llm_config=get_writer_agent_config()
        )
        
        # Content Editor Agents
        self.agents["blog_editor"] = AssistantAgent(
            name="BlogEditorAgent",
            system_message=BLOG_EDITOR_PROMPT,
            llm_config=get_editor_agent_config()
        )
        
        self.agents["linkedin_editor"] = AssistantAgent(
            name="LinkedInEditorAgent",
            system_message=LINKEDIN_EDITOR_PROMPT,
            llm_config=get_editor_agent_config()
        )
        
        self.agents["twitter_editor"] = AssistantAgent(
            name="TwitterEditorAgent",
            system_message=TWITTER_EDITOR_PROMPT,
            llm_config=get_editor_agent_config()
        )
    
    def setup_extraction_group(self):
        """Set up the extraction group chat."""
        extraction_members = [
            self.agents["user_proxy"],
            self.agents["extraction"]
        ]
        
        self.group_chats["extraction"] = GroupChat(
            agents=extraction_members,
            messages=[],
            max_round=10
        )
        
        return GroupChatManager(
            groupchat=self.group_chats["extraction"],
            llm_config=get_extraction_agent_config()
        )
    
    def setup_refinement_group(self):
        """Set up the transcript refinement group chat."""
        refinement_members = [
            self.agents["user_proxy"],
            self.agents["refiner"]
        ]
        
        self.group_chats["refinement"] = GroupChat(
            agents=refinement_members,
            messages=[],
            max_round=10
        )
        
        return GroupChatManager(
            groupchat=self.group_chats["refinement"],
            llm_config=get_refiner_agent_config()
        )
    
    def setup_topic_generation_group(self):
        """Set up the topic generation group chat."""
        topic_gen_members = [
            self.agents["user_proxy"],
            self.agents["topic_generator"]
        ]
        
        self.group_chats["topic_generation"] = GroupChat(
            agents=topic_gen_members,
            messages=[],
            max_round=10
        )
        
        return GroupChatManager(
            groupchat=self.group_chats["topic_generation"],
            llm_config=get_topic_generator_config()
        )
    
    def setup_content_creation_group(self, content_type):
        """
        Set up a content creation group chat for a specific content type.
        
        Args:
            content_type (str): Type of content to create ('blog', 'linkedin', or 'twitter')
        """
        if content_type not in ["blog", "linkedin", "twitter"]:
            raise ValueError("Content type must be 'blog', 'linkedin', or 'twitter'")
        
        writer_agent = self.agents[f"{content_type}_writer"]
        editor_agent = self.agents[f"{content_type}_editor"]
        
        creation_members = [
            self.agents["user_proxy"],
            writer_agent,
            editor_agent
        ]
        
        self.group_chats[f"{content_type}_creation"] = GroupChat(
            agents=creation_members,
            messages=[],
            max_round=10
        )
        
        return GroupChatManager(
            groupchat=self.group_chats[f"{content_type}_creation"],
            llm_config=get_writer_agent_config()
        )
    
    def process_youtube_url(self, youtube_url):
        """
        Process a YouTube URL through the complete pipeline.
        
        Args:
            youtube_url (str): The YouTube URL to process
            
        Returns:
            dict: The final content data with all generated content
        """
        # Store the URL
        self.content_data["video_url"] = youtube_url
        
        # Step 1: Extract transcript
        logging.info("Step 1: Extracting transcript from YouTube URL")
        extraction_manager = self.setup_extraction_group()
        extraction_manager.initiate_chat(
            self.agents["user_proxy"],
            message=f"Please extract the transcript from this YouTube URL: {youtube_url}"
        )
        
        # Process extraction results (to be implemented based on how results are handled)
        # For now, we'll manually call the extract function for demonstration
        extraction_result = extract_youtube_transcript(youtube_url)
        if not extraction_result["success"]:
            logging.error(f"Transcript extraction failed: {extraction_result.get('error', 'Unknown error')}")
            return {
                "success": False,
                "error": extraction_result.get('error', 'Unknown error')
            }
        
        # Store video info and transcript
        self.content_data["video_info"] = extraction_result.get("video_info", {})
        self.content_data["transcript"] = extraction_result.get("transcript", "")
        
        # Step 2: Refine transcript
        logging.info("Step 2: Refining the transcript")
        refinement_manager = self.setup_refinement_group()
        refinement_manager.initiate_chat(
            self.agents["user_proxy"],
            message=f"Please refine the following transcript:\n\n{self.content_data['transcript'][:2000]}..."
        )
        
        # Process refinement results (to be implemented based on how results are handled)
        # For now, we'll manually call the refine function for demonstration
        refinement_result = refine_transcript(self.content_data["transcript"])
        if not refinement_result["success"]:
            logging.error(f"Transcript refinement failed: {refinement_result.get('error', 'Unknown error')}")
            return {
                "success": False,
                "error": refinement_result.get('error', 'Unknown error')
            }
        
        # Store refined transcript
        self.content_data["refined_transcript"] = refinement_result.get("refined_transcript", "")
        
        # Step 3: Generate topics
        logging.info("Step 3: Generating content topics")
        topic_gen_manager = self.setup_topic_generation_group()
        topic_gen_manager.initiate_chat(
            self.agents["user_proxy"],
            message=f"Please generate content topics based on this refined transcript:\n\n{self.content_data['refined_transcript'][:2000]}..."
        )
        
        # Process topic generation results (to be implemented based on how results are handled)
        # For now, we'll manually call the generate_content_topics function for demonstration
        topics_result = generate_content_topics(self.content_data["refined_transcript"])
        if not topics_result["success"]:
            logging.error(f"Topic generation failed: {topics_result.get('error', 'Unknown error')}")
            return {
                "success": False,
                "error": topics_result.get('error', 'Unknown error')
            }
        
        # Store topics
        self.content_data["topics"] = topics_result.get("topics", {})
        
        # Step 4: Generate and edit content for each platform
        for platform in ["blog", "linkedin", "twitter"]:
            logging.info(f"Step 4: Generating {platform} content")
            
            # Get topics for this platform
            platform_topics = self.content_data["topics"].get(f"{platform}_topics", [])
            
            # Setup content creation group for this platform
            creation_manager = self.setup_content_creation_group(platform)
            
            for topic in platform_topics:
                # Initiate content creation
                creation_manager.initiate_chat(
                    self.agents["user_proxy"],
                    message=f"Please create {platform} content for the topic: {topic.get('title', 'Unknown Topic')}\n\nTopic description: {topic.get('description', 'No description')}"
                )
                
                # Process content creation results (to be implemented based on how results are handled)
                # For now, we'll manually generate and edit content for demonstration
                
                # Generate content
                if platform == "blog":
                    content_result = generate_blog_post(topic, self.content_data["refined_transcript"])
                elif platform == "linkedin":
                    content_result = generate_linkedin_post(topic, self.content_data["refined_transcript"])
                elif platform == "twitter":
                    content_result = generate_twitter_post(topic, self.content_data["refined_transcript"])
                
                if not content_result["success"]:
                    logging.warning(f"{platform} content generation failed for topic: {topic.get('title', 'Unknown')}")
                    continue
                
                # Edit content
                if platform == "blog":
                    edit_result = edit_blog_post(content_result)
                elif platform == "linkedin":
                    edit_result = edit_linkedin_post(content_result)
                elif platform == "twitter":
                    edit_result = edit_twitter_post(content_result)
                
                if not edit_result["success"]:
                    logging.warning(f"{platform} content editing failed for topic: {topic.get('title', 'Unknown')}")
                    # Use unedited content if editing fails
                    edit_result = content_result
                    edit_result["edited_content"] = edit_result["content"]
                
                # Store the content
                self.content_data[f"{platform}_posts"].append(edit_result)
        
        # Step 5: Save all content to file
        logging.info("Step 5: Saving all repurposed content to file")
        save_result = save_output(self.content_data)
        
        if not save_result["success"]:
            logging.error(f"Failed to save output: {save_result.get('error', 'Unknown error')}")
            return {
                "success": False,
                "error": save_result.get('error', 'Unknown error')
            }
        
        return {
            "success": True,
            "content_data": self.content_data,
            "output_file": save_result.get("file_path")
        }

def create_repurposer_system():
    """Factory function to create a RepurposerAgentSystem instance."""
    return RepurposerAgentSystem()

# Unit tests for RepurposerAgentSystem
def test_repurposer_agent_system():
    """Test the RepurposerAgentSystem class."""
    try:
        # Create a mock RepurposerAgentSystem instance
        system = RepurposerAgentSystem()
        
        # Test that all agents are created
        expected_agents = [
            "user_proxy", "extraction", "refiner", "topic_generator",
            "blog_writer", "linkedin_writer", "twitter_writer",
            "blog_editor", "linkedin_editor", "twitter_editor"
        ]
        
        for agent_name in expected_agents:
            assert agent_name in system.agents, f"Missing agent: {agent_name}"
        
        # Test group chat setup
        extraction_manager = system.setup_extraction_group()
        assert "extraction" in system.group_chats
        assert extraction_manager is not None
        
        refinement_manager = system.setup_refinement_group()
        assert "refinement" in system.group_chats
        assert refinement_manager is not None
        
        topic_gen_manager = system.setup_topic_generation_group()
        assert "topic_generation" in system.group_chats
        assert topic_gen_manager is not None
        
        # Test content creation group setup
        for platform in ["blog", "linkedin", "twitter"]:
            creation_manager = system.setup_content_creation_group(platform)
            assert f"{platform}_creation" in system.group_chats
            assert creation_manager is not None
        
        print("RepurposerAgentSystem tests passed!")
        return True
    
    except Exception as e:
        print(f"RepurposerAgentSystem test failed: {str(e)}")
        return False

if __name__ == "__main__":
    # Run tests when module is executed directly
    test_repurposer_agent_system()