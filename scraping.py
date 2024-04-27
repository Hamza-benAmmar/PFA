import os
import requests
from datetime import datetime
import json

# Load Instagram API configuration
with open('config.json', 'r') as f:
    config = json.load(f)

instagram_account_id = config['instagram_account_id']
access_token = config['access_token']

def save_images_to_folder(user_data):
    username = user_data['username']
    # Replace or remove problematic characters from the username
    clean_username = ''.join(c for c in username if c.isalnum() or c in {' ', '_', '-'}).rstrip()
    user_folder = os.path.join('images', clean_username)
    if not os.path.exists(user_folder):
        os.makedirs(user_folder)    
    # Save images
    for post in user_data['posts']:
        media_type = post['media_type']
        media_url = post.get('media_url', '') 
        if media_type == 'VIDEO':
            thumbnail_url = post.get('thumbnail_url', '')  
            image_url = thumbnail_url
        else:
            image_url = media_url

        if image_url:
            timestamp = datetime.strptime(post['timestamp'], "%Y-%m-%dT%H:%M:%S+0000")
            timestamp_seconds = int(timestamp.timestamp())
            image_path = os.path.join(user_folder, f"{timestamp_seconds}.jpg")
            with open(image_path, 'wb') as img_file:
                img_file.write(requests.get(image_url).content)
        else:
            print("Warning: 'media_url' not found for a post.")
            
# Function to get user info and posts
def get_user_info_and_posts(username, instagram_account_id, access_token):
    ig_params = {
        'fields': 'business_discovery.username(' + username + '){followers_count,media_count,name,media.limit(100){media_type,thumbnail_url,media_url,timestamp,caption,comments_count,like_count}}',
        'access_token': access_token
    }
    endpoint = f"https://graph.facebook.com/v19.0/{instagram_account_id}"
    response = requests.get(endpoint, params=ig_params)
    return format_response(response.json())

# Function to format the response
def format_response(response):
    user = {}
    try:
        business_discovery_data = response.get('business_discovery', {})
        user['username'] = business_discovery_data.get('name', '')
        user['user_id'] = business_discovery_data.get('id', '')
        user['followers_count'] = business_discovery_data.get('followers_count', 0)
        user['posts_count'] = business_discovery_data.get('media_count', 0)
        user['posts'] = business_discovery_data.get('media', {}).get('data', [])
        save_images_to_folder(user)
    except KeyError as e:
        print("KeyError:", e)
    return user

# Load usernames and interests from the JSON file
with open('output_interests.json', 'r') as f:
    interests_data = json.load(f)

json_filename = 'users.json'

# Check if the JSON file exists
if os.path.exists(json_filename):
    # Load existing data from the JSON file
    with open(json_filename, 'r') as f:
        existing_data = json.load(f)
else:
    existing_data = []

# Get user info and posts for each username, limiting to the first 30 users
counter = 0
for username, interests in interests_data.items():
    if counter >= 10:
        break
    user_data = get_user_info_and_posts(username, instagram_account_id, access_token)
    user_data['interests'] = interests
    print(user_data)
    existing_data.append(user_data)
    counter += 1

# Write the updated data back to the JSON file
with open(json_filename, 'w') as f:
    json.dump(existing_data, f, indent=4)

print("User data for the first 30 users has been saved to", json_filename)
