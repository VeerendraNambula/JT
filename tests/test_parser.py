from src.linkedin.ingest import LinkedInPost
from src.linkedin.job_parser import JobParser, heuristic_parse_job_details

def test_heuristic_parser():
    post = LinkedInPost(
        post_id="post_1",
        author_name="Alice",
        text_content=(
            "We are hiring at Google!\n"
            "Role: AI Engineer\n"
            "Location: Bengaluru, India\n"
            "Experience: 3+ years\n"
            "Salary: 25-35 LPA\n"
            "Apply here: https://google.com/careers"
        )
    )
    
    details = heuristic_parse_job_details(post)
    assert details.role == "AI Engineer"
    assert details.company == "Google"
    assert "Bengaluru" in details.location
    assert "3+" in details.experience_level
    assert "25-35 LPA" in details.salary
    assert details.apply_link == "https://google.com/careers"

def test_job_parser_with_fallback():
    # If API key is not configured, JobParser falls back to heuristic_parse_job_details
    parser = JobParser()
    post = LinkedInPost(
        post_id="post_2",
        author_name="Bob",
        text_content="We are hiring at Microsoft! Role: Frontend Engineer. Location: Pune."
    )
    details = parser.parse_job_details(post)
    assert details.role == "Frontend Engineer"
    assert details.company == "Microsoft"
    assert "Pune" in details.location
