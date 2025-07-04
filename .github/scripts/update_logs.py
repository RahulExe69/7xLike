import json
import os
from datetime import datetime
import pytz
from bs4 import BeautifulSoup

def update_logs_html():
    """Update the HTML logs page with the latest run results"""
    # Load the most recent run log
    try:
        with open('logs/latest_run.json', 'r') as f:
            latest_run = json.load(f)
    except FileNotFoundError:
        print("No latest run log found.")
        return False
        
    # Load the HTML template
    try:
        with open('logs.html', 'r') as f:
            soup = BeautifulSoup(f, 'html.parser')
    except FileNotFoundError:
        # Create a basic HTML if it doesn't exist
        soup = BeautifulSoup('''
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>7xLike - Daily Logs</title>
            <style>
                body {
                    font-family: Arial, sans-serif;
                    max-width: 800px;
                    margin: 0 auto;
                    padding: 20px;
                    background-color: #f0f2f5;
                }
                h1, h2 {
                    color: #4267B2;
                    text-align: center;
                }
                .log-container {
                    background-color: #fff;
                    border-radius: 8px;
                    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                    padding: 20px;
                    margin-bottom: 20px;
                }
                .log-entry {
                    border-left: 4px solid #4267B2;
                    padding: 10px;
                    margin-bottom: 15px;
                    background-color: #f7f7f7;
                }
                .log-date {
                    font-weight: bold;
                    color: #4267B2;
                }
                .log-details {
                    margin-top: 5px;
                    line-height: 1.5;
                }
                .success {
                    color: green;
                }
                .error {
                    color: red;
                }
                .player-info {
                    margin-top: 10px;
                    padding-left: 15px;
                    border-left: 2px solid #ddd;
                }
            </style>
        </head>
        <body>
            <h1>7xLike - Daily Activity Logs</h1>
            <div class="log-container">
                <h2>Recent Activity</h2>
                <div id="logs-content">
                </div>
            </div>
        </body>
        </html>
        ''', 'html.parser')
    
    # Get logs content div
    logs_content = soup.find(id="logs-content")
    
    # If logs content div doesn't exist, create it
    if not logs_content:
        logs_container = soup.find("div", class_="log-container")
        if not logs_container:
            logs_container = soup.new_tag("div")
            logs_container["class"] = "log-container"
            soup.body.append(logs_container)
            
        logs_content = soup.new_tag("div")
        logs_content["id"] = "logs-content"
        logs_container.append(logs_content)
    
    # Create new log entry
    log_entry = soup.new_tag("div")
    log_entry["class"] = "log-entry"
    
    log_date = soup.new_tag("div")
    log_date["class"] = "log-date"
    log_date.string = f"Run Time: {latest_run['run_time']}"
    log_entry.append(log_date)
    
    log_details = soup.new_tag("div")
    log_details["class"] = "log-details"
    
    # Add details for each processed user
    for result in latest_run["results"]:
        uid_div = soup.new_tag("div")
        if result["success"]:
            uid_div["class"] = "success"
            uid_div.string = f"✅ UID: {result['uid']} ({result['server']}): Success"
        else:
            uid_div["class"] = "error"
            uid_div.string = f"❌ UID: {result['uid']} ({result['server']}): Failed - {result.get('error', 'Unknown error')}"
        log_details.append(uid_div)
        
        # Add player details if successful
        if result["success"]:
            player_info = soup.new_tag("div")
            player_info["class"] = "player-info"
            player_info.string = f"Player: {result['player_name']} | Likes Given: {result['likes_given']} | Before: {result['likes_before']} | After: {result['likes_after']}"
            log_details.append(player_info)
    
    log_entry.append(log_details)
    
    # Insert the new log entry at the top
    first_entry = logs_content.find("div", class_="log-entry")
    if first_entry:
        first_entry.insert_before(log_entry)
    else:
        logs_content.append(log_entry)
    
    # Limit to 30 entries to keep the file size reasonable
    entries = logs_content.find_all("div", class_="log-entry")
    if len(entries) > 10:
        for i in range(10, len(entries)):
            entries[i].decompose()
    
    # Save the updated HTML
    with open('logs.html', 'w') as f:
        f.write(str(soup))
    
    return True

if __name__ == "__main__":
    update_logs_html()
    print("HTML logs updated successfully!")
