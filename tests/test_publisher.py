import pytest
from unittest.mock import MagicMock, patch
from src.twitter.publisher import XPublisher

@patch("tweepy.Client")
@patch("src.twitter.publisher.settings")
def test_publisher_initialization(mock_settings, mock_tweepy_client):
    # Setup mock credentials
    mock_settings.x_api_key = "test_key"
    mock_settings.x_api_secret = "test_secret"
    mock_settings.x_access_token = "test_token"
    mock_settings.x_access_token_secret = "test_token_secret"
    
    publisher = XPublisher()
    
    assert publisher.is_configured() is True
    mock_tweepy_client.assert_called_once_with(
        consumer_key="test_key",
        consumer_secret="test_secret",
        access_token="test_token",
        access_token_secret="test_token_secret"
    )

@patch("tweepy.Client")
@patch("src.twitter.publisher.settings")
def test_publisher_not_configured_when_credentials_missing(mock_settings, mock_tweepy_client):
    # Missing some credentials
    mock_settings.x_api_key = "test_key"
    mock_settings.x_api_secret = None
    mock_settings.x_access_token = "test_token"
    mock_settings.x_access_token_secret = None
    
    publisher = XPublisher()
    
    assert publisher.is_configured() is False
    mock_tweepy_client.assert_not_called()

@patch("tweepy.Client")
@patch("src.twitter.publisher.settings")
def test_publish_tweet_success(mock_settings, mock_tweepy_client):
    mock_settings.x_api_key = "k"
    mock_settings.x_api_secret = "s"
    mock_settings.x_access_token = "t"
    mock_settings.x_access_token_secret = "ts"
    
    # Mock tweepy client instance
    mock_instance = MagicMock()
    mock_tweepy_client.return_value = mock_instance
    
    # Mock return value of create_tweet
    mock_response = MagicMock()
    mock_response.data = {"id": "1234567890"}
    mock_instance.create_tweet.return_value = mock_response
    
    publisher = XPublisher()
    tweet_id = publisher.publish_tweet("Hello world!")
    
    assert tweet_id == "1234567890"
    mock_instance.create_tweet.assert_called_once_with(text="Hello world!")

@patch("tweepy.Client")
@patch("src.twitter.publisher.settings")
def test_publish_tweet_failure(mock_settings, mock_tweepy_client):
    mock_settings.x_api_key = "k"
    mock_settings.x_api_secret = "s"
    mock_settings.x_access_token = "t"
    mock_settings.x_access_token_secret = "ts"
    
    mock_instance = MagicMock()
    mock_tweepy_client.return_value = mock_instance
    mock_instance.create_tweet.side_effect = Exception("API Error")
    
    publisher = XPublisher()
    tweet_id = publisher.publish_tweet("Hello world!")
    
    assert tweet_id is None
    mock_instance.create_tweet.assert_called_once_with(text="Hello world!")
