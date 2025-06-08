#!/usr/bin/env python3
import json
import requests
import os
import logging
import concurrent.futures
from datetime import datetime
import pytz

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("token_updater")

# API URL for token generation
TOKEN_GEN_URL = "https://7x-gen.vercel.app/token"

# Maximum number of concurrent requests
MAX_CONCURRENT_REQUESTS = 10
# Request timeout in seconds
REQUEST_TIMEOUT = 10

def get_new_token(account):
    """Get a new JWT token for a given account"""
    uid = account.get('uid')
    password = account.get('password')
    
    try:
        url = f"{TOKEN_GEN_URL}?uid={uid}&password={password}"
        response = requests.get(url, timeout=REQUEST_TIMEOUT)
        
        if response.status_code == 200:
            # Parse the response to extract just the JWT token
            try:
                # First, try to parse it as JSON to see if it contains a token field
                response_data = response.json()
                if isinstance(response_data, dict) and "token" in response_data:
                    # Extract just the token value from JSON
                    token = response_data["token"]
                else:
                    # If it's not a dict with token field, use the raw text
                    token = response.text.strip()
            except:
                # If JSON parsing fails, use the raw text
                token = response.text.strip()
                
            logger.info(f"Successfully generated token for UID: {uid}")
            return {"uid": uid, "token": token}
        else:
            logger.error(f"Failed to get token for UID {uid}: HTTP {response.status_code}")
            logger.error(f"Response: {response.text}")
            return {"uid": uid, "error": f"HTTP {response.status_code}"}
    except Exception as e:
        logger.error(f"Error fetching token for UID {uid}: {str(e)}")
        return {"uid": uid, "error": str(e)}

def update_tokens():
    """Update JWT tokens for all accounts using concurrent requests"""
    current_time = datetime.now(pytz.timezone('Asia/Kolkata')).strftime("%Y-%m-%d %H:%M:%S")
    logger.info(f"Starting token update at {current_time}")
    
    try:
        # Read accounts from environment variable or fallback to file
        if 'ACCOUNTS_JSON' in os.environ:
            accounts_json = os.environ.get('ACCOUNTS_JSON')
            accounts = json.loads(accounts_json)
            logger.info("Using accounts from environment variables")
        else:
            # Fallback to file-based approach
            with open('accounts.json', 'r') as f:
                accounts = json.load(f)
            logger.info("Using accounts from accounts.json file")
        
        logger.info(f"Found {len(accounts)} accounts to update")
        
        # Generate new tokens concurrently
        new_tokens = []
        with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_CONCURRENT_REQUESTS) as executor:
            # Submit all requests
            future_to_account = {executor.submit(get_new_token, account): account for account in accounts}
            
            # Process results as they complete
            for future in concurrent.futures.as_completed(future_to_account):
                result = future.result()
                if "token" in result:
                    new_tokens.append({"token": result["token"]})
                else:
                    logger.error(f"Failed to generate token for UID {result['uid']}: {result.get('error', 'Unknown error')}")
        
        # Update token_ind.json with new tokens
        if new_tokens:
            with open('token_ind.json', 'w') as f:
                json.dump(new_tokens, f, indent=2)
            logger.info(f"Successfully updated token_ind.json with {len(new_tokens)} tokens")
        else:
            logger.error("No tokens were generated. token_ind.json not updated.")
            
    except Exception as e:
        logger.error(f"Error during token update process: {str(e)}")
        raise e  # Rethrow the exception to ensure workflow fails

if __name__ == "__main__":
    update_tokens()
