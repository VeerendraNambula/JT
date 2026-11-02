from src.linkedin.ingest import JobDetails
from src.twitter.tweet_generator import TweetGenerator


def test_tweet_never_exceeds_x_limit_with_extreme_fields():
    job = JobDetails(
        role="Senior " * 30,
        company="Example Company " * 20,
        location="Hyderabad, Telangana, India " * 15,
        experience_level="Minimum 15+ years " * 15,
        salary="25-40 LPA " * 20,
        apply_link="https://example.com/jobs/123",
    )
    tweet = TweetGenerator().generate_tweet(job)
    assert TweetGenerator.get_x_length(tweet) <= 280
    assert "https://example.com/jobs/123" in tweet


def test_tweet_keeps_short_complete_announcement():
    job = JobDetails(
        role="AI Engineer",
        company="Example Labs",
        location="Hyderabad",
        experience_level="0-2 years",
        salary="6-10 LPA",
        apply_link="https://example.com/jobs/ai",
    )
    tweet = TweetGenerator().generate_tweet(job)
    assert "AI Engineer" in tweet
    assert "Example Labs" in tweet
    assert "#AI" in tweet
