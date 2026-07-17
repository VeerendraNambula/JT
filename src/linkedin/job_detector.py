import logging
from google import genai
from google.genai import types
from pydantic import BaseModel
from src.linkedin.ingest import LinkedInPost
from src.config.settings import settings

logger = logging.getLogger(__name__)

class JobDetection(BaseModel):
    is_job: bool

class JobDetector:
    """
    Classifies if a post represents a job opening.
    Uses Gemini LLM if GEMINI_API_KEY is present and use_llm is True;
    otherwise, falls back to a keyword-based heuristic.
    """
    def __init__(self, use_llm: bool = True):
        self.use_llm = use_llm
        self.client = None
        if self.use_llm and settings.gemini_api_key:
            try:
                self.client = genai.Client(api_key=settings.gemini_api_key)
            except Exception as e:
                logger.warning(f"Failed to initialize Gemini Client: {e}. Falling back to heuristics.")

    def is_job_opening(self, post: LinkedInPost) -> bool:
        """
        Determines if a post represents a job announcement.
        """
        # Heuristics check
        text_lower = post.text_content.lower()
        
        # Self-promotion / career update negations
        negations = [
            "started a new role", "started as", "excited to share that i", 
            "happy to share that i", "joined as", "joined the team as", 
            "congratulate", "thrilled to share", "im happy to announce"
        ]
        
        if any(neg in text_lower for neg in negations):
            has_keyword = False
        else:
            keywords = [
                "hiring", "recruiting", "open position", "looking for a", 
                "join our team", "we are looking", "immediate requirement", 
                "immediate vacancy", "opening for", "careers", 
                "employment opportunity", "apply now", "hiring for"
            ]
            has_keyword = any(k in text_lower for k in keywords)
        
        # If client is configured and use_llm is true, use LLM
        if self.use_llm and self.client:
            try:
                response = self.client.models.generate_content(
                    model=settings.default_model,
                    contents=(
                        "Analyze the following social media post and determine if it represents a job opening, "
                        "hiring announcement, or immediate vacancy. Ignore news posts about general hiring trends "
                        "or general advice.\n\n"
                        f"Post Text:\n{post.text_content}"
                    ),
                    config=types.GenerateContentConfig(
                        response_mime_type="application/json",
                        response_schema=JobDetection,
                    ),
                )
                
                if response.text:
                    # Clean response.text from potential markdown if LLM misbehaves (unlikely with MIME setting)
                    cleaned_text = response.text.strip()
                    if cleaned_text.startswith("```json"):
                        cleaned_text = cleaned_text[7:]
                    if cleaned_text.endswith("```"):
                        cleaned_text = cleaned_text[:-3]
                    cleaned_text = cleaned_text.strip()
                    
                    result = JobDetection.model_validate_json(cleaned_text)
                    return result.is_job
            except Exception as e:
                logger.error(f"Error during LLM job detection: {e}. Falling back to heuristics.")
                
        # Fallback to heuristics
        return has_keyword
