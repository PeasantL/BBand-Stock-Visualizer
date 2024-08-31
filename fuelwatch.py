import feedparser
import requests
import urllib.parse  # To properly encode URL parameters

# Set the locations
locations = ["Osborne Park", "Canning Vale"]

# Parse function from API
def get_fuel(location, tomorrow=False):
    params = {
        'Product': 1,
        'Suburb': location,
        'Day': 'tomorrow' if tomorrow else 'today'
    }
    response = requests.get("http://www.fuelwatch.wa.gov.au/fuelwatch/fuelWatchRSS", params=params, headers={"user-agent": "Mozilla/5.0"})
    feed = feedparser.parse(response.content)

    if feed['entries']:
        # Custom logic for Canning Vale to select specific address
        if location == "Canning Vale":
            for entry in feed['entries']:
                if entry.get("address") == "6 Birnam Rd":
                    return {
                        "location": entry["location"],
                        "address": entry["address"],
                        "brand": entry["brand"],
                        "price": entry["price"],
                        "date": "Tomorrow" if tomorrow else "Today",
                    }
        # Default behavior for other locations
        else:
            entry = feed['entries'][0]
            return {
                "location": entry["location"],
                "address": entry["address"],
                "brand": entry["brand"],
                "price": entry["price"],
                "date": "Tomorrow" if tomorrow else "Today",
            }
    return None  # Return None if no entry found

def generate_fuel_content():
    # Prepare data dictionary
    data = {location: {'Today': None, 'Tomorrow': None} for location in locations}

    # Fetch and organize data
    for location in locations:
        data[location]['Today'] = get_fuel(location)
        data[location]['Tomorrow'] = get_fuel(location, tomorrow=True)

    # Prepare HTML content with CSS
    my_html_tdst = '''
    <style>
        #fuelTable, #fuelTable th, #fuelTable td {
            border: 1px solid black;
            border-collapse: collapse;
        }
        #fuelTable th, #fuelTable td {
            padding: 8px;
            text-align: left;
        }
    </style>
    <tr><td class='content'>
    <h3>Fuel Watch</h3>
    <table id='fuelTable'>
    <thead>
    <tr>
        <th></th>
        <th>Osborne Park</th>
        <th>Canning Vale</th>
    </tr>
    </thead>
    <tbody>
    '''

    # Add rows for Today and Tomorrow
    for day in ['Today', 'Tomorrow']:
        my_html_tdst += f'<tr><td>{day}</td>'
        for location in locations:
            if data[location][day]:
                encoded_address = urllib.parse.quote_plus(data[location][day]["address"])
                map_link = f"https://www.google.com/maps/search/?api=1&query={encoded_address}"
                my_html_tdst += f'''
                <td>
                    <a href="{map_link}" target="_blank">{data[location][day]["address"]}</a><br>
                    {data[location][day]["brand"]}<br>
                    {data[location][day]["price"]} cpl<br>
                </td>
                '''
            else:
                my_html_tdst += '<td>N/A</td>'
        my_html_tdst += '</tr>'

    my_html_tdst += '''
    </tbody>
    </table>
    </tr></td>
    '''

    return my_html_tdst
