from src.linkedin.ingest import LinkedInPost
from src.linkedin.job_detector import JobDetector

def test_heuristic_job_detection():
    detector = JobDetector(use_llm=False)
    
    job_post = LinkedInPost(
        post_id="post_1",
        author_name="Alice Smith",
        text_content="We are hiring a new machine learning researcher! Apply now."
    )
    
    non_job_post = LinkedInPost(
        post_id="post_2",
        author_name="Bob Jones",
        text_content="Just had a wonderful coffee chat with some engineers."
    )
    
    assert detector.is_job_opening(job_post) is True
    assert detector.is_job_opening(non_job_post) is False
