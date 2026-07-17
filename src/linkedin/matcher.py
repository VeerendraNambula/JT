import re
from typing import Optional, Tuple
from src.linkedin.ingest import JobDetails

class JobMatcher:
    @staticmethod
    def parse_experience_range(exp_str: Optional[str]) -> Tuple[Optional[float], Optional[float]]:
        """
        Parses years of experience required from a string.
        Returns a tuple of (min_years, max_years).
        None represents no limit (e.g. max_years=None means no upper bound).
        """
        if not exp_str:
            return None, None
            
        clean_str = exp_str.lower().strip()
        
        # Check for fresher/internship indicators
        if "fresher" in clean_str or "intern" in clean_str or "0 yr" in clean_str or "0 year" in clean_str:
            return 0.0, 1.0
            
        # Find all numbers (matches integers and decimals)
        numbers = [float(n) for n in re.findall(r'\b\d+(?:\.\d+)?\b', clean_str)]
        
        if not numbers:
            return None, None
            
        # If we have a range like 1-5 years
        if len(numbers) >= 2:
            return min(numbers), max(numbers)
            
        # If we have a single number, check if "+" or "above" or "at least" is present
        # e.g., "2+ years", "2 years min", "at least 3 years"
        num = numbers[0]
        if "+" in clean_str or "above" in clean_str or "at least" in clean_str or "min" in clean_str or "more" in clean_str:
            return num, None
            
        # Default single number to minimum required
        return num, None

    @staticmethod
    def match_job(details: JobDetails, target_role: str, target_exp: float) -> bool:
        """
        Validates if a job announcement matches the user's target role and experience.
        """
        if not target_role:
            return True
            
        target_role_clean = target_role.lower().strip()
        role_clean = details.role.lower().strip() if details.role else ""
        
        # Split target_role into words to allow partial keyword matching (e.g. "Software Engineer" matches "Senior Software Engineer")
        target_words = [w for w in re.split(r'\W+', target_role_clean) if w]
        if not target_words:
            return True
            
        # Check if ALL words of target_role are present in the job role
        role_matched = all(word in role_clean for word in target_words)
        if not role_matched:
            return False
            
        # 2. Experience Match
        min_years, max_years = JobMatcher.parse_experience_range(details.experience_level)
        
        # If experience is unspecified, match by default
        if min_years is None and max_years is None:
            return True
            
        if min_years is not None and target_exp < min_years:
            return False
            
        if max_years is not None and target_exp > max_years:
            return False
            
        return True
