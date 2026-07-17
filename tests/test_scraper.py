import pytest
from unittest.mock import MagicMock, patch
from src.linkedin.scraper import LinkedInScraper

@patch("src.linkedin.scraper.sync_playwright")
def test_fetch_posts_mock(mock_sync_playwright):
    # Setup mocks for Playwright sync API
    mock_playwright = MagicMock()
    mock_sync_playwright.return_value.__enter__.return_value = mock_playwright
    
    mock_context = MagicMock()
    mock_playwright.chromium.launch_persistent_context.return_value = mock_context
    
    mock_page = MagicMock()
    mock_context.new_page.return_value = mock_page
    mock_page.url = "https://www.linkedin.com/company/somecompany/posts/"
    
    # Mock update card items
    mock_card = MagicMock()
    mock_card.get_attribute.return_value = "urn:li:activity:70001"
    
    mock_text = MagicMock()
    mock_text.inner_text.return_value = "We are hiring! Join us as an AI Architect in Bengaluru. Exp: 5+ years. Apply at https://jobs.company.com"
    
    mock_author = MagicMock()
    mock_author.inner_text.return_value = "Some Company"
    
    mock_link = MagicMock()
    mock_link.get_attribute.return_value = "/feed/update/urn:li:activity:70001"
    
    mock_date = MagicMock()
    mock_date.inner_text.return_value = "1 day ago • Edited"
    
    mock_profile = MagicMock()
    mock_profile.get_attribute.return_value = "/company/somecompany"
    
    # Setup card.query_selector mapping
    def query_selector_mock(selector):
        if ".feed-shared-text" in selector or ".commentary" in selector:
            return mock_text
        if "span.feed-shared-actor__title" in selector or ".actor__name" in selector:
            return mock_author
        if "a[href*='/feed/update/']" in selector:
            return mock_link
        if ".feed-shared-actor__sub-text" in selector:
            return mock_date
        if "a[href*='/company/']" in selector:
            return mock_profile
        return None
        
    mock_card.query_selector.side_effect = query_selector_mock
    
    # Let page.query_selector_all return our mock card when selectors are queried
    mock_page.query_selector_all.return_value = [mock_card]
    
    posts = LinkedInScraper.fetch_posts("https://www.linkedin.com/company/somecompany/posts")
    
    assert len(posts) == 1
    post = posts[0]
    assert post.post_id == "70001"
    assert post.author_name == "Some Company"
    assert "AI Architect" in post.text_content
    assert post.post_url == "https://www.linkedin.com/feed/update/urn:li:activity:70001"
    assert post.posted_date == "1 day ago"
    assert post.author_profile_url == "https://www.linkedin.com/company/somecompany"
