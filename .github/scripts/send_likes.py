import requests
import logging
import time
import json
import os
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
    {"uid": "661067880", "server_name": "IND"},
    {"uid": "1830656132", "server_name": "IND"},
    {"uid": "1322681052", "server_name": "IND"},
    {"uid": "1852957153", "server_name": "IND"}
]

# API URL
API_BASE_URL = "https://7x-like.vercel.app/like"

# Create logs directory if it doesn't exist
os.makedirs("logs", exist_ok=True)

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
            return {
                "success": True,
                "uid": uid,
                "server": server_name,
                "timestamp": datetime.now(pytz.timezone('Asia/Kolkata')).strftime("%Y-%m-%d %H:%M:%S"),
                "likes_given": result.get('LikesGivenByAPI', 0),
                "likes_before": result.get('LikesbeforeCommand', 0),
                "likes_after": result.get('LikesafterCommand', 0),
                "player_name": result.get('PlayerNickname', 'Unknown'),
            }
        else:
            logger.error(f"Failed with status code: {response.status_code}, Response: {response.text}")
            return {
                "success": False,
                "uid": uid,
                "server": server_name,
                "timestamp": datetime.now(pytz.timezone('Asia/Kolkata')).strftime("%Y-%m-%d %H:%M:%S"),
                "error": f"Failed with status code: {response.status_code}"
            }
        
    except Exception as e:
        logger.error(f"Error sending likes to UID {uid}: {str(e)}")
        return {
            "success": False,
            "uid": uid,
            "server": server_name,
            "timestamp": datetime.now(pytz.timezone('Asia/Kolkata')).strftime("%Y-%m-%d %H:%M:%S"),
            "error": str(e)
        }

def main():
    current_time = datetime.now(pytz.timezone('Asia/Kolkata')).strftime("%Y-%m-%d %H:%M:%S")
    logger.info(f"GitHub Actions job running. Current time in India: {current_time}")
    
    # Create a log entry for this run
    log_entry = {
        "run_time": current_time,
        "results": []
    }
    
    for user in USERS_TO_LIKE:
        result = send_likes(user["uid"], user["server_name"])
        log_entry["results"].append(result)
        
        if result["success"]:
            logger.info(f"Successfully processed UID {user['uid']}")
        else:
            logger.error(f"Failed to process UID {user['uid']}")
    
    logger.info("GitHub Actions job completed")
    
    # Save the log entry for this run
    log_file = "logs/latest_run.json"
    with open(log_file, 'w') as f:
        json.dump(log_entry, f, indent=2)

if __name__ == "__main__":
    main()
