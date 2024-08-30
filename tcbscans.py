import requests
from bs4 import BeautifulSoup

# URL of the page
url = 'https://tcbscans.me/mangas/5/one-piece'

# Send a GET request
response = requests.get(url)
response.raise_for_status()  # This will raise an error if the request failed

# Parse the HTML content
soup = BeautifulSoup(response.text, 'html.parser')

# Find all chapter entries using the class 'block' that also seems to be a part of each chapter entry
chapters = soup.find_all('a', class_='block')

# Extract chapter titles and URLs
newest_chapter = chapters[0] if chapters else None

if newest_chapter:
    chapter_title = newest_chapter.find('div', class_='text-lg font-bold').get_text(strip=True)
    chapter_subtitle = newest_chapter.find('div', class_='text-gray-500').get_text(strip=True)
    chapter_url = 'https://tcbscans.me' + newest_chapter['href']
    print(f"Newest Chapter: {chapter_title} - {chapter_subtitle}")
    print(f"URL: {chapter_url}")
else:
    print("No chapters found.")
