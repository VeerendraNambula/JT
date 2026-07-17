from datetime import datetime
from typing import Optional, List
import json
import csv
from pydantic import BaseModel, Field

class LinkedInPost(BaseModel):
    post_id: str = Field(..., description="Unique identifier for the post")
    author_name: str = Field(..., description="Name of the person who posted")
    author_profile_url: Optional[str] = None
    post_url: Optional[str] = Field(None, description="Direct link to the LinkedIn post")
    text_content: str = Field(..., description="Raw text body of the post")
    posted_date: Optional[str] = None  # Using string representation for simplified parsing

class JobDetails(BaseModel):
    role: str = Field(..., description="Job title, e.g., AI/ML Engineer, Full-Stack Developer")
    company: str = Field(..., description="Company hiring, or 'Unspecified'")
    location: str = Field(..., description="Primary location, focusing on India (e.g., Bengaluru, Remote)")
    experience_level: str = Field(..., description="Experience required (e.g., Entry-level, 3+ years, Senior)")
    salary: Optional[str] = Field(None, description="Compensation info if mentioned, otherwise None")
    apply_link: Optional[str] = Field(None, description="Email, link, or contact instruction to apply")

class ProcessingResult(BaseModel):
    post: LinkedInPost
    is_job: bool
    job_details: Optional[JobDetails] = None
    tweet_text: Optional[str] = None

def ingest_posts_from_json(file_path: str) -> List[LinkedInPost]:
    with open(file_path, "r", encoding="utf-8") as f:
        raw_data = json.load(f)
    
    posts = []
    if isinstance(raw_data, dict):
        raw_data = [raw_data]
        
    for item in raw_data:
        posts.append(
            LinkedInPost(
                post_id=str(item.get("post_id") or item.get("id") or ""),
                author_name=item.get("author_name") or item.get("author") or "Unknown",
                author_profile_url=item.get("author_profile_url"),
                post_url=item.get("post_url") or item.get("url"),
                text_content=item.get("text_content") or item.get("text") or "",
                posted_date=item.get("posted_date") or item.get("date")
            )
        )
    return posts

def ingest_posts_from_csv(file_path: str) -> List[LinkedInPost]:
    posts = []
    with open(file_path, "r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            posts.append(
                LinkedInPost(
                    post_id=row.get("post_id") or row.get("id") or "",
                    author_name=row.get("author_name") or row.get("author") or "Unknown",
                    author_profile_url=row.get("author_profile_url"),
                    post_url=row.get("post_url") or row.get("url"),
                    text_content=row.get("text_content") or row.get("text") or "",
                    posted_date=row.get("posted_date") or row.get("date")
                )
            )
    return posts

def ingest_raw_posts(file_path: str) -> List[LinkedInPost]:
    """
    Ingests posts from JSON or CSV file based on file extension.
    """
    if file_path.lower().endswith(".csv"):
        return ingest_posts_from_csv(file_path)
    else:
        return ingest_posts_from_json(file_path)
