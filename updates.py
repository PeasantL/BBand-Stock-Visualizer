from ebay import get_ebay_results
from github import get_status_updates
import toml
from datetime import datetime
from send_email import send_email_with_attachment

# Load settings from the TOML file
config = toml.load("settings.toml")

# Email settings
sender_email = config['email']['sender_email']
receiver_email = config['email']['receiver_email']
password = config['email']['password']

date_now = datetime.now().strftime('%d/%m/%Y')

subject = date_now + " Update Report"


def create_email_content():
    
    email_body = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Email Template</title>
        <style>
            body {
                font-family: Arial, sans-serif;
                margin: 0;
                padding: 0;
                background-color: #f4f4f4;
            }
            table {
                max-width: 800px;
                margin: auto;
                background-color: #ffffff;
                border-collapse: collapse;
                border-spacing: 0;
                box-shadow: 0 0 10px rgba(0, 0, 0, 0.1);
            }
            .header {
                background-color: #0073e6;
                color: white;
                padding: 20px;
                text-align: center;
            }
            .content {
                padding: 20px;
                color: #333333;
            }
            .footer {
                background-color: #f4f4f4;
                color: #777777;
                padding: 10px;
                text-align: center;
                font-size: 12px;
            }
            a {
                color: #0073e6;
                text-decoration: none;
            }
        </style>
    </head>
    <body>
        <table>
            <tr>
                <td class="header">
                    <h1>%s</h1>
                </td>
            </tr>
            %s
            <tr>
                <td class="footer">
                    <p>PeasantL/Info-Mail-Bot</p>
                    <p><a href="https://github.com/PeasantL/Info-Mail-Bot">https://github.com/PeasantL/Info-Mail-Bot</a></p>
                </td>
            </tr>
        </table>
    </body>
    </html>
    """ % (subject, modules_run())
    return email_body

def modules_run():
    return get_status_updates() + "<tr><td><hr></td></tr>" + get_ebay_results()

email_body = create_email_content()
send_email_with_attachment(subject, sender_email, receiver_email, password, email_body)
