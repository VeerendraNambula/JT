import pytest
from unittest.mock import patch

from src.linkedin.scraper import LinkedInScraper


@pytest.mark.parametrize(
    "url",
    [
        "http://www.linkedin.com/company/example/posts",
        "https://example.com/",
        "https://linkedin.com.evil.example/",
        "file:///etc/passwd",
    ],
)
def test_scraper_rejects_non_linkedin_or_non_https_urls(url):
    with patch("src.linkedin.scraper.sync_playwright") as playwright:
        with pytest.raises(ValueError, match="HTTPS LinkedIn"):
            LinkedInScraper.fetch_posts(url)
        playwright.assert_not_called()


def test_scraper_rejects_non_positive_limits():
    with pytest.raises(ValueError, match="must be positive"):
        LinkedInScraper.fetch_posts("https://www.linkedin.com/company/example/posts", limit=0)
