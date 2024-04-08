import praw
import os
from dotenv import load_dotenv

load_dotenv()


def get_client():
    username = os.getenv("REDDIT_USERNAME")
    return praw.Reddit(
        client_id=os.getenv("REDDIT_CLIENT_ID"),
        client_secret=os.getenv("REDDIT_SECRET"),
        password=os.getenv("REDDIT_PASSWORD"),
        user_agent=f"python:counter-hate-detection-script:1.0.0 (by /u/{username})",
        username=os.getenv("REDDIT_USERNAME"),
    )