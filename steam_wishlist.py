import requests
from bs4 import BeautifulSoup
import json

def fetch_steam_wishlist():
    url = "https://store.steampowered.com/search/?filter=popularwishlist"
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'}

    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.text, 'html.parser')

    games = [game.text for game in soup.find_all('span', class_='title')[:10]]
    return games

def load_previous_list(file_path):
    try:
        with open(file_path, 'r') as file:
            return json.load(file)
    except FileNotFoundError:
        return []

def save_current_list(games, file_path):
    with open(file_path, 'w') as file:
        json.dump(games, file, indent=4)

def track_changes(current_games, previous_games):
    return [(game, game not in previous_games) for game in current_games]

def get_tracked_games_html():
    json_file_path = 'steam_games.json'
    previous_games = load_previous_list(json_file_path)
    current_games = fetch_steam_wishlist()
    tracked_games = track_changes(current_games, previous_games)

    save_current_list(current_games, json_file_path)

    results_output = "<tr><td class='content'>"
    results_output += "<h3>Top Steam Wishlist Games</h3>"
    for i, (game, is_new) in enumerate(tracked_games[:10]):  # Limiting to top 10 games for display
        new_mark = " (New!)" if is_new else ""
        output = f"{i + 1}. {game}{new_mark}<br><br>"
        results_output += output
    results_output += "</td></tr>"
    return results_output

# Example of how you might use this function in another part of your application
# print(get_tracked_games_html())
