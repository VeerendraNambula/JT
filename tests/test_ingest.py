import os
import json
import pytest
from src.linkedin.ingest import LinkedInPost, JobDetails, ingest_raw_posts

def test_linkedin_post_model():
    post = LinkedInPost(
        post_id="post_1",
        author_name="Alice Smith",
        post_url="https://linkedin.com/posts/alice-1",
        text_content="We are hiring an AI Engineer!"
    )
    assert post.post_id == "post_1"
    assert post.author_name == "Alice Smith"
    assert "AI Engineer" in post.text_content

def test_ingest_json_file(tmp_path):
    # Setup temp JSON file
    sample_data = [
        {
            "id": "post_1",
            "author": "Alice Smith",
            "url": "https://linkedin.com/posts/alice-1",
            "text": "We are hiring an AI Engineer!",
            "date": "2026-07-17T00:00:00Z"
        },
        {
            "post_id": "post_2",
            "author_name": "Bob Jones",
            "post_url": "https://linkedin.com/posts/bob-2",
            "text_content": "Just had an amazing lunch.",
            "posted_date": "2026-07-17T12:00:00Z"
        }
    ]
    
    file_path = os.path.join(tmp_path, "posts.json")
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(sample_data, f)
        
    posts = ingest_raw_posts(file_path)
    assert len(posts) == 2
    assert posts[0].post_id == "post_1"
    assert posts[0].author_name == "Alice Smith"
    assert posts[1].post_id == "post_2"
    assert posts[1].author_name == "Bob Jones"
