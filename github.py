import requests
import json
import toml

# List of repositories to track
repositories = [
    "theroyallab/tabbyAPI",
    "SillyTavern/SillyTavern",
    "LostRuins/koboldcpp",
    "oobabooga/text-generation-webui"
]

config = toml.load("settings.toml")

# Your GitHub personal access token
access_token = config['github']['auth_token']

# Headers to use in the API request
headers = {
    'Authorization': f'token {access_token}',
    'Accept': 'application/vnd.github.v3+json'
}

# Base URL for GitHub API
base_url = 'https://api.github.com/repos/'

# File to store the last known releases and commits
tracking_file = 'tracking_data.json'

# Load the last known releases and commits from file
try:
    with open(tracking_file, 'r') as file:
        tracking_data = json.load(file)
except FileNotFoundError:
    tracking_data = {}

# Function to get the latest commit from the default branch
def get_latest_commit(repo):
    url = f"{base_url}{repo}/commits"
    params = {'per_page': 1}  # Fetch only the latest commit
    response = requests.get(url, headers=headers, params=params)
    if response.status_code == 200:
        data = response.json()
        return data[0]['sha'], data[0]['commit']['message']  # Return the SHA and message of the latest commit
    else:
        return None, None

# Function to get the latest release or commit
def get_latest_release_or_commit(repo):
    url = f"{base_url}{repo}/releases/latest"
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        data = response.json()
        return 'release', data.get('id'), data.get('tag_name')  # Returning type, ID, and tag name (version)
    elif response.status_code == 404:
        # If no release found, fetch the latest commit
        commit_id, commit_message = get_latest_commit(repo)
        if commit_id:
            return 'commit', commit_id, commit_message  # Return the commit message instead of SHA
        else:
            return 'error', None, None
    else:
        return 'error', None, None

# Function to collect status updates as a string
def get_status_updates():
    status_updates = "<tr><td class='content'>"
    status_updates += f"<h3>Github Repo Updates</h3>"
    for repo in repositories:
        item_type, item_id, item_name = get_latest_release_or_commit(repo)
        repo_link = f"https://github.com/{repo}"  # Creating link to the repository
        if item_type != 'error' and item_id:
            if repo not in tracking_data or tracking_data[repo] != item_id:
                if item_type == 'release':
                    status_updates += f"<a href='{repo_link}'>{repo}</a><br>New release<br>Version: {item_name}<br><br>"
                else:
                    status_updates += f"<a href='{repo_link}'>{repo}</a><br>New commit<br>Message: {item_name}<br><br>"
                tracking_data[repo] = item_id
            else:
                if item_type == 'release':
                    status_updates += f"<a href='{repo_link}'>{repo}</a><br>No new release<br>Current Version: {item_name}<br><br>"
                else:
                    status_updates += f"<a href='{repo_link}'>{repo}</a><br>No new commit<br>Current Message: {item_name}<br><br>"
        else:
            status_updates += f"<a href='{repo_link}'>{repo}</a><br>No release or commit information available.<br><br>"
    
    status_updates += "</td></tr>"

    # Save the updated tracking data to file
    with open(tracking_file, 'w') as file:
        json.dump(tracking_data, file)

    return ''.join(status_updates)
