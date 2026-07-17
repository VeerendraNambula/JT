from src.linkedin.ingest import LinkedInPost
from src.linkedin.job_detector import JobDetector

def test_heuristic_job_detection():
    detector = JobDetector(use_llm=False)
    
    job_post = LinkedInPost(
        post_id="post_1",
        author_name="Alice Smith",
        text_content="We are hiring a new machine learning researcher! Apply now at careers@company.com"
    )
    
    gmail_job_post = LinkedInPost(
        post_id="post_2",
        author_name="Charlie Brown",
        text_content="We are hiring a new designer! Send your resume to charlie@gmail.com"
    )
    
    no_email_job_post = LinkedInPost(
        post_id="post_3",
        author_name="Dave Miller",
        text_content="We are hiring a developer. Please click the link to apply."
    )
    
    non_job_post = LinkedInPost(
        post_id="post_4",
        author_name="Bob Jones",
        text_content="Just had a wonderful coffee chat with some engineers."
    )
    
    assert detector.is_job_opening(job_post) is True
    assert detector.is_job_opening(gmail_job_post) is False
    assert detector.is_job_opening(no_email_job_post) is False
    assert detector.is_job_opening(non_job_post) is False
