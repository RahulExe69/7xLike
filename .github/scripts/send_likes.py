import requests
import logging
import time
from datetime import datetime
import pytz

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("github_like_sender")

# UIDs to send likes to
USERS_TO_LIKE = [
    {"uid": "651948621", "server_name": "IND"},
    {"uid": "661067880", "server_name": "IND"}
]

# API URL
API_BASE_URL = "https://7x-like.vercel.app/like"

def send_likes(uid, server_name):
    """Send likes to a specific UID using the deployed API"""
    try:
        api_url = f"{API_BASE_URL}?uid={uid}&server_name={server_name}"
        logger.info(f"Sending likes to UID {uid} on server {server_name}")
        logger.info(f"API URL: {api_url}")
        
        # Add a small delay to avoid rate limiting
        time.sleep(1)
        
        # Make the API request
        response = requests.get(api_url)
        
        if response.status_code == 200:
            result = response.json()
            logger.info(f"Successfully sent {result.get('LikesGivenByAPI', 0)} likes to {result.get('PlayerNickname', 'Unknown')}")
            logger.info(f"Likes before: {result.get('LikesbeforeCommand', 0)}, Likes after: {result.get('LikesafterCommand', 0)}")
            return True
        else:
            logger.error(f"Failed with status code: {response.status_code}, Response: {response.text}")
            return False
        
    except Exception as e:
        logger.error(f"Error sending likes to UID {uid}: {str(e)}")
        return False

def main():
    current_time = datetime.now(pytz.timezone('Asia/Kolkata')).strftime("%Y-%m-%d %H:%M:%S")
    logger.info(f"GitHub Actions job running. Current time in India: {current_time}")
    
    for user in USERS_TO_LIKE:
        success = send_likes(user["uid"], user["server_name"])
        if success:
            logger.info(f"Successfully processed UID {user['uid']}")
        else:
            logger.error(f"Failed to process UID {user['uid']}")
    
    logger.info("GitHub Actions job completed")

if __name__ == "__main__":
    main()
