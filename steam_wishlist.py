import requests
from bs4 import BeautifulSoup
from track_data import open_json, save_json 

def fetch_steam_wishlist():
    url = "https://store.steampowered.com/search/?filter=popularwishlist"
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'}

    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.text, 'html.parser')

    games = []
    for game in soup.find_all('a', class_='search_result_row')[:10]:
        title = game.find('span', class_='title').text
        link = game['href']
        games.append({'title': title, 'link': link})
    
    return games

def track_changes(current_games, previous_games):
    previous_titles = [game['title'] for game in previous_games]
    return [(game, game['title'] not in previous_titles) for game in current_games]

def get_tracked_games_html():
    json_file_path = 'steam_wishlist.json'
    previous_games = open_json(json_file_path)  # Using open_json from track_data
    current_games = fetch_steam_wishlist()
    tracked_games = track_changes(current_games, previous_games)

    save_json(json_file_path, current_games)  # Using save_json from track_data

    results_output = "<tr><td class='content'>"
    results_output += "<h3>Top Steam Wishlist Games</h3>"
    for i, (game, is_new) in enumerate(tracked_games[:10]):  # Limiting to top 10 games for display
        new_mark = " (New!)" if is_new else ""
        output = f"{i + 1}. <a href='{game['link']}'>{game['title']}</a>{new_mark}<br><br>"
        results_output += output
    results_output += "</td></tr>"
    return results_output
