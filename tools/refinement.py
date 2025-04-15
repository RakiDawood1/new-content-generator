import re
import logging
import google.generativeai as genai
from dotenv import load_dotenv
import os

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

def clean_timestamps(text):
    """
    Remove timestamp patterns from the transcript text.
    
    Args:
        text (str): The transcript text containing timestamps
        
    Returns:
        str: Cleaned text with timestamps removed
    """
    # Remove [MM:SS] format timestamps
    text = re.sub(r'\[\d{1,2}:\d{2}\]', '', text)
    
    # Remove (MM:SS) format timestamps
    text = re.sub(r'\(\d{1,2}:\d{2}\)', '', text)
    
    # Remove HH:MM:SS format timestamps
    text = re.sub(r'\d{1,2}:\d{2}:\d{2}', '', text)
    
    # Remove any remaining timestamp-like patterns
    text = re.sub(r'\d{1,2}:\d{2}', '', text)
    
    return text.strip()

def clean_speaker_labels(text):
    """
    Standardize or remove speaker labels from the transcript text.
    
    Args:
        text (str): The transcript text containing speaker labels
        
    Returns:
        str: Cleaned text with standardized speaker labels
    """
    # Replace common speaker label patterns with standardized format
    # Example: "Speaker 1:", "[Speaker 1]", "(John):" -> "Speaker 1:"
    text = re.sub(r'\[Speaker\s*(\d+)\]', r'Speaker \1:', text)
    text = re.sub(r'\(Speaker\s*(\d+)\)', r'Speaker \1:', text)
    text = re.sub(r'\[([^\]]+)\]:', r'\1:', text)
    text = re.sub(r'\(([^\)]+)\):', r'\1:', text)
    
    # Ensure consistent spacing around speaker labels
    text = re.sub(r'(\w+:)\s*', r'\1 ', text)
    
    return text.strip()

def fix_punctuation(text):
    """
    Fix common punctuation issues in the transcript text.
    
    Args:
        text (str): The transcript text with punctuation issues
        
    Returns:
        str: Text with corrected punctuation
    """
    # Add space after periods if missing
    text = re.sub(r'\.(?=[A-Z])', '. ', text)
    
    # Add space after commas if missing
    text = re.sub(r',(?=\w)', ', ', text)
    
    # Fix multiple periods
    text = re.sub(r'\.{2,}', '...', text)
    
    # Fix multiple spaces
    text = re.sub(r'\s+', ' ', text)
    
    # Fix space before punctuation
    text = re.sub(r'\s+([.,!?])', r'\1', text)
    
    # Ensure single space after punctuation
    text = re.sub(r'([.,!?])\s*', r'\1 ', text)
    
    # Fix quotation marks spacing
    text = re.sub(r'\s*"\s*([^"]*)\s*"\s*', r' "\1" ', text)
    
    return text.strip()

def fix_capitalization(text):
    """
    Fix capitalization issues in the transcript text.
    
    Args:
        text (str): The transcript text with capitalization issues
        
    Returns:
        str: Text with corrected capitalization
    """
    # Split into sentences (considering multiple punctuation marks)
    sentences = re.split(r'([.!?]+)\s+', text)
    
    # Capitalize first letter of each sentence
    processed_sentences = []
    for i in range(0, len(sentences), 2):
        sentence = sentences[i]
        if sentence:
            # Capitalize first letter of the sentence
            sentence = sentence[0].upper() + sentence[1:] if len(sentence) > 1 else sentence.upper()
            processed_sentences.append(sentence)
        
        # Add back the punctuation and space if they exist
        if i + 1 < len(sentences):
            processed_sentences.append(sentences[i + 1] + ' ')
    
    # Join sentences back together
    text = ''.join(processed_sentences)
    
    # Capitalize common proper nouns (can be expanded based on needs)
    common_proper_nouns = ['i', 'i\'m', 'i\'ve', 'i\'ll', 'i\'d']
    for word in common_proper_nouns:
        text = re.sub(r'\b' + word + r'\b', word.capitalize(), text)
    
    return text.strip()

def remove_filler_words(text):
    """
    Remove or reduce common filler words from the transcript text.
    
    Args:
        text (str): The transcript text containing filler words
        
    Returns:
        str: Text with reduced filler words
    """
    # List of common filler words and phrases
    filler_words = [
        r'\bum\b', r'\buh\b', r'\blike\b(?!\s+to|\s+a|\s+the)',  # "like" only when not part of a verb phrase
        r'\byou know\b', r'\bi mean\b', r'\bso\b(?=\s+um|\s+uh)',
        r'\bbasically\b', r'\bliterally\b', r'\bactually\b(?=\s+um|\s+uh)',
        r'\bkind of\b(?=\s+um|\s+uh)', r'\bsort of\b(?=\s+um|\s+uh)',
        r'\bjust\b(?=\s+um|\s+uh)', r'\bright\b(?=\s+um|\s+uh)',
        r'\bwell\b(?=\s+um|\s+uh)', r'\byeah\b(?=\s+um|\s+uh)'
    ]
    
    # Remove filler words
    for filler in filler_words:
        text = re.sub(filler, '', text)
    
    # Fix any double spaces created by removal
    text = re.sub(r'\s+', ' ', text)
    
    return text.strip()

def refine_transcript_structure(text):
    """
    Improve the overall structure of the transcript text.
    
    Args:
        text (str): The transcript text to restructure
        
    Returns:
        str: Restructured transcript text
    """
    # Split text into paragraphs
    paragraphs = text.split('\n')
    
    # Process each paragraph
    processed_paragraphs = []
    current_paragraph = []
    
    for paragraph in paragraphs:
        paragraph = paragraph.strip()
        if not paragraph:
            if current_paragraph:
                processed_paragraphs.append(' '.join(current_paragraph))
                current_paragraph = []
            continue
        
        # Check if this is a new speaker
        if re.match(r'^[A-Za-z]+\s*:', paragraph):
            if current_paragraph:
                processed_paragraphs.append(' '.join(current_paragraph))
                current_paragraph = []
        
        current_paragraph.append(paragraph)
    
    # Add the last paragraph if exists
    if current_paragraph:
        processed_paragraphs.append(' '.join(current_paragraph))
    
    # Join paragraphs with proper spacing
    text = '\n\n'.join(processed_paragraphs)
    
    return text.strip()

def refine_with_gemini(text):
    """
    Use Gemini to improve the transcript text further.
    
    Args:
        text (str): The pre-processed transcript text
        
    Returns:
        dict: A dictionary containing the success status and refined text
    """
    try:
        # Create Gemini model instance
        gemini_model = genai.GenerativeModel(model_name="gemini-1.5-pro", temperature=0.3)
        
        # Prepare the prompt
        prompt = f"""
        Please refine this transcript text to improve clarity and readability while maintaining the original meaning.
        Focus on:
        1. Fixing any remaining grammatical errors
        2. Improving sentence structure and flow
        3. Ensuring clarity and coherence
        4. Maintaining the speaker's voice and intent
        5. Preserving technical terms and specific references
        
        Original transcript:
        {text}
        
        Return only the refined text without any explanations or markup.
        """
        
        response = gemini_model.generate_content(prompt)
        
        if response and hasattr(response, 'text'):
            refined_text = response.text.strip()
            return {
                "success": True,
                "text": refined_text
            }
        else:
            return {
                "success": False,
                "error": "Failed to get valid response from Gemini"
            }
    
    except Exception as e:
        logging.error(f"Error during Gemini refinement: {str(e)}")
        return {
            "success": False,
            "error": f"Gemini refinement error: {str(e)}"
        }

def refine_transcript(transcript_text):
    """
    Main function to refine a transcript using all available refinement methods.
    
    Args:
        transcript_text (str): The raw transcript text to refine
        
    Returns:
        dict: A dictionary containing the success status and refined transcript
    """
    if not transcript_text or transcript_text.strip() == "":
        return {
            "success": False,
            "error": "Empty transcript provided"
        }
    
    try:
        logging.info("Starting transcript refinement")
        
        # Step 1: Clean timestamps
        logging.info("Removing timestamps...")
        text = clean_timestamps(transcript_text)
        
        # Step 2: Clean speaker labels
        logging.info("Standardizing speaker labels...")
        text = clean_speaker_labels(text)
        
        # Step 3: Fix punctuation
        logging.info("Fixing punctuation...")
        text = fix_punctuation(text)
        
        # Step 4: Fix capitalization
        logging.info("Fixing capitalization...")
        text = fix_capitalization(text)
        
        # Step 5: Remove filler words
        logging.info("Removing filler words...")
        text = remove_filler_words(text)
        
        # Step 6: Improve structure
        logging.info("Improving transcript structure...")
        text = refine_transcript_structure(text)
        
        # Step 7: Final refinement with Gemini
        logging.info("Performing final refinement with Gemini...")
        gemini_result = refine_with_gemini(text)
        
        if not gemini_result["success"]:
            logging.warning("Gemini refinement failed, using pre-Gemini version")
            final_text = text
        else:
            final_text = gemini_result["text"]
        
        return {
            "success": True,
            "original_transcript": transcript_text,
            "refined_transcript": final_text
        }
    
    except Exception as e:
        logging.error(f"Error during transcript refinement: {str(e)}")
        return {
            "success": False,
            "error": f"Refinement error: {str(e)}"
        }

# Unit tests
def test_transcript_refinement():
    """Test the transcript refinement functions."""
    # Test data
    test_transcript = """
    [00:15] Speaker 1: um, yeah, so like I wanted to talk about, you know, the importance of AI...
    
    [00:30] speaker 2: i think that's a great topic actually... um... let me share my thoughts
    
    [00:45] Speaker 1: yeah,yeah,definitely. AI is changing everything,right? like,it's so amazing...
    """
    
    try:
        print("\nTesting transcript refinement functions...")
        
        # Test timestamp cleaning
        cleaned_timestamps = clean_timestamps(test_transcript)
        assert "[00:15]" not in cleaned_timestamps
        print("✓ Timestamp cleaning passed")
        
        # Test speaker label cleaning
        cleaned_speakers = clean_speaker_labels(test_transcript)
        assert "Speaker 1:" in cleaned_speakers
        assert "speaker 2:" not in cleaned_speakers  # Should be standardized
        print("✓ Speaker label cleaning passed")
        
        # Test punctuation fixing
        fixed_punctuation = fix_punctuation("Hello,world.How are you.I'm good")
        assert "Hello, world. How are you. I'm good" in fixed_punctuation
        print("✓ Punctuation fixing passed")
        
        # Test capitalization fixing
        fixed_caps = fix_capitalization("hello. world. how are you? i'm good")
        assert "Hello. World. How are you? I'm good" in fixed_caps
        print("✓ Capitalization fixing passed")
        
        # Test filler word removal
        cleaned_fillers = remove_filler_words("Um, like, you know, it's important")
        assert "um" not in cleaned_fillers.lower()
        assert "like" not in cleaned_fillers.lower()
        print("✓ Filler word removal passed")
        
        # Test complete refinement
        result = refine_transcript(test_transcript)
        assert result["success"] == True
        assert result["refined_transcript"] != test_transcript
        print("✓ Complete refinement passed")
        
        print("\nAll transcript refinement tests passed!")
        return True
    
    except AssertionError as e:
        print(f"Test failed: {str(e)}")
        return False
    except Exception as e:
        print(f"Error during testing: {str(e)}")
        return False

if __name__ == "__main__":
    # Run tests when module is executed directly
    test_transcript_refinement()