import logging
import tweepy
from typing import Optional
from src.config.settings import settings

logger = logging.getLogger(__name__)

class XPublisher:
    """
    Handles publishing tweets to Twitter/X using tweepy's v2 Client interface.
    """
    def __init__(self):
        self.client = None
        # Check if all four required credentials are provided
        if all([
            settings.x_api_key,
            settings.x_api_secret,
            settings.x_access_token,
            settings.x_access_token_secret
        ]):
            try:
                self.client = tweepy.Client(
                    consumer_key=settings.x_api_key,
                    consumer_secret=settings.x_api_secret,
                    access_token=settings.x_access_token,
                    access_token_secret=settings.x_access_token_secret
                )
                logger.info("Successfully initialized X/Twitter Publisher client.")
            except Exception as e:
                logger.error(f"Failed to initialize tweepy Client: {e}")
        else:
            logger.warning(
                "X/Twitter Publisher not configured. "
                "Ensure X_API_KEY, X_API_SECRET, X_ACCESS_TOKEN, and X_ACCESS_TOKEN_SECRET are set."
            )

    def is_configured(self) -> bool:
        """
        Returns True if the publisher is fully authenticated and ready.
        """
        return self.client is not None

    def publish_tweet(self, text: str) -> Optional[str]:
        """
        Publishes a tweet to X. Returns the tweet ID (str) if successful, otherwise None.
        """
        if not self.client:
            logger.warning("Attempted to publish tweet, but XPublisher is not configured.")
            return None

        try:
            response = self.client.create_tweet(text=text)
            tweet_id = response.data.get("id") if response.data else None
            if tweet_id:
                logger.info(f"Successfully posted tweet to X (Tweet ID: {tweet_id})")
                return str(tweet_id)
            else:
                logger.error(f"Failed to publish tweet. Response data was empty: {response}")
                return None
        except Exception as e:
            logger.error(f"Error publishing tweet to X: {e}")
            return None
