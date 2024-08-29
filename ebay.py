import requests
from bs4 import BeautifulSoup

def scrape_ebay(search_query):
    # Replace spaces with '+', as eBay uses this format for search queries
    search_query = search_query.replace(' ', '+')
    # Base URL
    url = f"https://www.ebay.com.au/sch/i.html"

    # Parameters for the GET request
    params = {
        '_from': 'R40',
        '_nkw': search_query,
        '_sacat': '0',
        'LH_BIN': '1',
        'LH_PrefLoc': '1',
        '_sop': '15'
    }
    
    headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36',
    'Accept-Language': 'en-US,en;q=0.9',
    'Accept-Encoding': 'gzip, deflate, br',
    'Referer': 'https://www.ebay.com.au/'
    }

    # Send a GET request to eBay
    response = requests.get(url, params=params, headers=headers)
    
    # Check if the request was successful
    if response.status_code != 200:
        print(f"Failed to retrieve data: {response.status_code}")
        return []

    
    # Parse the HTML content
    soup = BeautifulSoup(response.content, 'html.parser')

    # Find all items
    items = soup.find_all('li', {'class': 's-item'})

    results = []
    
    for item in items:
        title = price = link = None  # Initialize variables to avoid referencing before assignment
        # Extract the title
        title_tag = item.find('div', {'class': 's-item__title'})
        if title_tag:
            title = title_tag.get_text().strip()

        # Extract the price
        price_tag = item.find('span', {'class': 's-item__price'})
        if price_tag:
            price = price_tag.get_text().strip()

        # Extract the link
        link_tag = item.find('a', {'class': 's-item__link'})
        if link_tag:
            link = link_tag['href']

        # Append the results if all details are present
        if title and price and link:
            results.append({
                'title': title,
                'price': price,
                'link': link
            })
    return results

def preprocess_results(results):
    # Remove the first two entries
    filtered_results = results[2:] if len(results) > 2 else []

    # Ensure prices are in ascending order and remove entries as soon as they are not
    if not filtered_results:
        return filtered_results

    final_results = []
    # Parse the first price correctly removing the currency symbol and commas
    last_price = parse_price(filtered_results[0]['price'])

    for item in filtered_results:
        current_price = parse_price(item['price'])

        if current_price >= last_price:
            final_results.append(item)
            last_price = current_price
        else:
            break

    return final_results

def parse_price(price_str):
    # Remove currency symbols, commas, and convert to float
    return float(price_str.replace('AU $', '').replace(',', ''))

def get_ebay_results():
    search_term = "rtx 3090"
    ebay_results = scrape_ebay(search_term)
    preprocessed_results = preprocess_results(ebay_results)

    results_output = "<tr><td class='content'>"
    results_output += f"<h3>Ebay Search: {search_term}</h3>"
    for result in preprocessed_results[:5]:
        output = (
            f"<strong>{result['title']}</strong><br>"
            f"Price: {result['price']}<br>"
            f"Link: <a href='{result['link']}'>{'Click Here'}</a><br><br>"
        )
        results_output += output
    results_output += "</td></tr>"
    return results_output
