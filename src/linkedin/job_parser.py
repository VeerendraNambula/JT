import logging
import re
from typing import Optional
from google import genai
from google.genai import types
from src.linkedin.ingest import LinkedInPost, JobDetails
from src.config.settings import settings

logger = logging.getLogger(__name__)

def clean_extracted_field(field_val: str) -> str:
    """
    Trims any trailing field labels that were accidentally captured on the same line.
    """
    delimiters = [
        r"\bcompany\b", r"\bat\b", r"\brole\b", r"\bposition\b", r"\btitle\b", 
        r"\blocation\b", r"\bloc\b", r"\bworkplace\b", r"\bexperience\b", 
        r"\bexp\b", r"\byoe\b", r"\bsalary\b", r"\bctc\b", r"\bcompensation\b", 
        r"\bpackage\b", r"\blpa\b", r"\bapply\b"
    ]
    cleaned = field_val
    for delim in delimiters:
        match = re.search(delim + r"\s*:", cleaned, re.IGNORECASE)
        if match:
            cleaned = cleaned[:match.start()].strip()
            
    # Remove trailing punctuation
    cleaned = re.sub(r"[.,;|]+$", "", cleaned).strip()
    return cleaned

def heuristic_parse_job_details(post: LinkedInPost) -> JobDetails:
    """
    Fallback regex-based heuristic parsing when LLM is unavailable.
    """
    text = post.text_content
    text_lower = text.lower()
    
    # 1. Extract role
    role = "Software Engineer"
    role_match = re.search(r"(?:role|position|title|hiring for a|hiring for)\s*:\s*([^\n\r]+)", text, re.IGNORECASE)
    if role_match:
        role = clean_extracted_field(role_match.group(1))
    else:
        # Check standard role names
        roles = ["ai engineer", "ml engineer", "machine learning engineer", "data scientist", "full stack developer", "full-stack developer", "backend engineer", "frontend engineer", "software engineer", "devops engineer", "product manager", "data engineer"]
        for r in roles:
            if r in text_lower:
                role = r.title()
                break
                
    # 2. Extract company
    company = "Unspecified"
    company_match = re.search(r"(?:company|at|hiring at)\s*:\s*([^\n\r]+)", text, re.IGNORECASE)
    if company_match:
        company = clean_extracted_field(company_match.group(1))
    else:
        at_match = re.search(r"\bhiring at\s+([A-Z][a-zA-Z0-9_]+)", text)
        if at_match:
            company = at_match.group(1).strip()
            
    # 3. Extract location
    location = "India"
    loc_match = re.search(r"(?:location|loc|workplace)\s*:\s*([^\n\r]+)", text, re.IGNORECASE)
    if loc_match:
        location = clean_extracted_field(loc_match.group(1))
    else:
        cities = ["bengaluru", "bangalore", "pune", "hyderabad", "mumbai", "noida", "delhi", "chennai", "gurugram", "gurgaon", "remote"]
        found_cities = []
        for c in cities:
            if c in text_lower:
                found_cities.append(c.title() if c not in ["bangalore", "bengaluru"] else "Bengaluru")
        if found_cities:
            location = ", ".join(list(set(found_cities)))
            
    # 4. Extract experience
    experience = "Not Specified"
    exp_match = re.search(r"(?:experience|exp|yoe)\s*:\s*([^\n\r]+)", text, re.IGNORECASE)
    if exp_match:
        experience = clean_extracted_field(exp_match.group(1))
    else:
        yoe_match = re.search(r"(\d+\s*[-+to]*\s*\d*\s*(?:years?|yrs?)(?:\s*of\s*exp(?:erience)?)?)", text, re.IGNORECASE)
        if yoe_match:
            experience = clean_extracted_field(yoe_match.group(1))
            
    # 5. Extract salary
    salary = None
    sal_match = re.search(r"(?:salary|ctc|compensation|package|lpa)\s*:\s*([^\n\r]+)", text, re.IGNORECASE)
    if sal_match:
        salary = clean_extracted_field(sal_match.group(1))
    else:
        lpa_match = re.search(r"(\d+\s*-\s*\d+\s*(?:lpa|ctc|lakhs?))", text, re.IGNORECASE)
        if lpa_match:
            salary = clean_extracted_field(lpa_match.group(1))

            
    # 6. Extract apply link
    apply_link = post.post_url
    urls = re.findall(r"(https?://[^\s]+)", text)
    if urls:
        apply_link = urls[0]
    else:
        email_match = re.search(r"([a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+)", text)
        if email_match:
            apply_link = f"mailto:{email_match.group(1).strip()}"
            
    return JobDetails(
        role=role,
        company=company,
        location=location,
        experience_level=experience,
        salary=salary,
        apply_link=apply_link
    )

class JobParser:
    """
    Parses LinkedIn post content to extract job attributes.
    Utilizes Gemini structured schema output for high reliability,
    falling back to regular expression parsing when keys are absent.
    """
    def __init__(self):
        self.client = None
        if settings.gemini_api_key:
            try:
                self.client = genai.Client(api_key=settings.gemini_api_key)
            except Exception as e:
                logger.warning(f"Failed to initialize Gemini Client: {e}. Falling back to heuristics.")

    def parse_job_details(self, post: LinkedInPost) -> JobDetails:
        """
        Parses job details from LinkedInPost content.
        """
        if self.client:
            try:
                response = self.client.models.generate_content(
                    model=settings.default_model,
                    contents=(
                        "Extract the job details from the following post. "
                        "Identify the role, hiring company, location, experience required, "
                        "salary or compensation if mentioned, and apply link or email.\n\n"
                        f"Post Text:\n{post.text_content}\n\n"
                        f"Post URL: {post.post_url or 'None'}"
                    ),
                    config=types.GenerateContentConfig(
                        response_mime_type="application/json",
                        response_schema=JobDetails,
                    ),
                )
                if response.text:
                    cleaned_text = response.text.strip()
                    if cleaned_text.startswith("```json"):
                        cleaned_text = cleaned_text[7:]
                    if cleaned_text.endswith("```"):
                        cleaned_text = cleaned_text[:-3]
                    cleaned_text = cleaned_text.strip()
                    
                    details = JobDetails.model_validate_json(cleaned_text)
                    if not details.apply_link and post.post_url:
                        details = details.model_copy(update={"apply_link": post.post_url})
                    return details
            except Exception as e:
                logger.error(f"Error during LLM job parsing: {e}. Falling back to heuristics.")
                
        # Default fallback
        details = heuristic_parse_job_details(post)
        if not details.apply_link and post.post_url:
            details = details.model_copy(update={"apply_link": post.post_url})
        return details
