import requests
from bs4 import BeautifulSoup
from track_data import open_json, save_json

def scrape_huggingface_models():
    tracking_file = 'huggingface.json'
    tracking_data = open_json(tracking_file)
    
    # The URL to scrape
    url = "https://huggingface.co/models?sort=trending&search=12b"

    # Send a GET request to the URL
    response = requests.get(url)

    if response.status_code == 200:
        # Parse the HTML content using BeautifulSoup
        soup = BeautifulSoup(response.content, "html.parser")
        
        # Find all the relevant article elements with the class 'overview-card-wrapper group/repo'
        models = soup.find_all("article", class_="overview-card-wrapper group/repo")
        
        # Initialize data storage for the current run
        current_data = {}
        html_output = "<tr><td class='content'><h3>Trending Hugging Face Models</h3>"
        
        # Index to track each model entry
        index = 1
        
        for model in models[:6]: 
            # Extract the link
            link = model.find("a", class_="flex items-center justify-between gap-4 p-2")['href']
            # Full link for correct redirection
            full_link = f"https://huggingface.co{link}"
            # Extract the title (assuming the title is in the link text)
            title = link.split("/")[-1]
            # Extract the release date
            release_date = model.find("time").text.strip()
            
            # Extract all SVG icons and their associated text
            svg_elements = model.find_all("svg", {"aria-hidden": "true"})
            svg_texts = [svg.find_next_sibling(string=True).strip() for svg in svg_elements]
            
            # Determine if 'type' is present (i.e., more than 2 SVG elements)
            if len(svg_texts) > 2:
                # Assume the first SVG is 'type' and discard it
                downloads = svg_texts[1]
                likes = svg_texts[2]
            else:
                # No 'type' present, so use the first two directly
                downloads = svg_texts[0]
                likes = svg_texts[1]
            
            # Check if this model is new compared to the previous data
            is_new = title not in tracking_data
            
            # Store the current data
            current_data[title] = {
                "link": full_link,
                "release_date": release_date,
                "downloads": downloads,
                "likes": likes
            }
            
            # Build the HTML output
            html_output += f'<div>{index}. <a href="{full_link}" target="_blank">{title}</a>'
            if is_new:
                html_output += " (New!)"
            html_output += f'<br>  Released: {release_date}<br>'
            html_output += f'  Downloads: {downloads}<br>'
            html_output += f'  Likes: {likes}<br><br></div>'
            
            # Increment the index for the next model
            index += 1
        
        html_output += "</tr></td>"
        
        # Update the tracking data with the current data
        save_json(tracking_file, current_data)  # Save the current data, not the original tracking data
        
        # Return the HTML string
        return html_output

    else:
        return f"<p>Failed to retrieve content. Status code: {response.status_code}</p>"
