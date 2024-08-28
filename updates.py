from ebay import get_ebay_results
from github import get_status_updates
import toml
from send_email import send_email_with_attachment

# Load settings from the TOML file
config = toml.load("settings.toml")

# Email settings
sender_email = config['email']['sender_email']
receiver_email = config['email']['receiver_email']
password = config['email']['password']

subject = f"Update Report"


def create_email_content():
    content = []
    content.append("Github Updates")
    content.append(get_status_updates())
    content.append("*" * 40)
    content.append("Ebay Scrape")
    content.append("RTX 3090")
    content.append(get_ebay_results())
    content.append("*" * 40)
    return "<br>".join(content)  # Convert list to HTML-compatible string

email_body = create_email_content()

send_email_with_attachment(subject, sender_email, receiver_email, password, email_body)
