from src.linkedin.ingest import JobDetails
from src.twitter.tweet_generator import TweetGenerator

def test_tweet_emoji_mapping():
    tweeter = TweetGenerator()
    
    ai_job = JobDetails(
        role="AI Researcher",
        company="Startup A",
        location="Bengaluru",
        experience_level="1-3 years",
        apply_link="https://startup-a.com"
    )
    
    dev_job = JobDetails(
        role="Fullstack Engineer",
        company="Startup B",
        location="Remote",
        experience_level="Senior",
        apply_link="https://startup-b.com"
    )
    
    ai_tweet = tweeter.generate_tweet(ai_job)
    dev_tweet = tweeter.generate_tweet(dev_job)
    
    assert "🤖" in ai_tweet
    assert "💻" in dev_tweet

def test_twitter_url_length_simulation():
    tweeter = TweetGenerator()
    long_url = "https://startup.com/some/very/long/url/path/to/apply/for/the/role/of/engineer/which/is/really/long"
    
    # Verify our custom length calculation simulates URLs as exactly 23 characters
    text = f"Apply here: {long_url}"
    # Simulated: "Apply here: " is 12 chars. + 23 chars. = 35 chars.
    assert tweeter.get_x_length(text) == 35

def test_progressive_truncation():
    tweeter = TweetGenerator()
    
    # Setup job details that would yield a very long tweet
    long_job = JobDetails(
        role="Super senior staff AI research engineer specializing in distributed systems training and optimization",
        company="Extremely Long Company Name That Takes Up Way Too Many Characters in a Tweet Inc.",
        location="Bengaluru, Karnataka, India - In-Office / Hybrid",
        experience_level="Minimum 15+ years of industry experience with PhD",
        salary="120-150 LPA base salary + benefits + stock options",
        apply_link="https://hiring-portal.extremely-long-domain-name-to-test-length.com/jobs/apply/12345"
    )
    
    tweet = tweeter.generate_tweet(long_job)
    
    # Assert tweet is <= 280 characters under simulated Twitter counting
    sim_len = tweeter.get_x_length(tweet)
    assert sim_len <= 280
    assert "🤖" in tweet
