import pytest
from src.linkedin.ingest import JobDetails
from src.linkedin.matcher import JobMatcher

def test_parse_experience_range():
    # Freshers
    assert JobMatcher.parse_experience_range("fresher") == (0.0, 1.0)
    assert JobMatcher.parse_experience_range("0-1 year") == (0.0, 1.0)
    
    # Ranges
    assert JobMatcher.parse_experience_range("1-3 years") == (1.0, 3.0)
    assert JobMatcher.parse_experience_range("2 to 5 Yrs") == (2.0, 5.0)
    
    # Plus ranges
    assert JobMatcher.parse_experience_range("2+ years") == (2.0, None)
    assert JobMatcher.parse_experience_range("min 3 years") == (3.0, None)
    
    # Unspecified
    assert JobMatcher.parse_experience_range("Not Specified") == (None, None)
    assert JobMatcher.parse_experience_range(None) == (None, None)

def test_match_job():
    job = JobDetails(
        role="Senior Software Engineer",
        company="TechCorp",
        location="Bangalore",
        experience_level="2-5 years",
        salary=None,
        apply_link="mailto:hr@techcorp.com"
    )
    
    # Matching cases
    assert JobMatcher.match_job(job, "Software Engineer", 3.0) is True
    assert JobMatcher.match_job(job, "software", 2.0) is True
    
    # Mismatching role
    assert JobMatcher.match_job(job, "Product Manager", 3.0) is False
    
    # Mismatching experience (too low)
    assert JobMatcher.match_job(job, "Software Engineer", 1.0) is False
    
    # Mismatching experience (too high)
    assert JobMatcher.match_job(job, "Software Engineer", 6.0) is False

def test_match_job_unspecified_experience():
    job = JobDetails(
        role="Python Developer",
        company="AI Labs",
        location="Remote",
        experience_level="Not Specified",
        salary=None,
        apply_link="mailto:hr@ailabs.com"
    )
    # Unspecified exp matches any input exp
    assert JobMatcher.match_job(job, "Python", 0.0) is True
    assert JobMatcher.match_job(job, "Python", 5.0) is True
