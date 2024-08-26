import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import pytz
import yfinance as yf
import matplotlib.pyplot as plt
import os
import toml
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders

# Load settings from the TOML file
config = toml.load("settings.toml")
tickers = config['tickers']['symbols']
years_back = config['analysis']['years_back']
#y_min = config['analysis']['y_min']
y_min = None

# Email settings
sender_email = config['email']['sender_email']
receiver_email = config['email']['receiver_email']
password = config['email']['password']
body = config['email']['body']

timezone = pytz.timezone('Australia/Perth')
current_time = datetime.now(timezone).strftime("%Y%m%d_%H%M%S")
subject = f"{datetime.now().strftime('%d/%m/%Y')} - Auto Stock Report"

def fetch_and_visualize(tickers, years_back=5, y_min=None):
    nrows, ncols = 2, 3
    email_details = {}
    plt.figure(figsize=(15, 5 * nrows))

    for i, ticker in enumerate(tickers):
        end_date = datetime.now()
        start_date = end_date - timedelta(days=365 * years_back)
        data = yf.download(ticker, start=start_date.strftime('%Y-%m-%d'), end=end_date.strftime('%Y-%m-%d'))
        data['Short_MA'] = data['Close'].rolling(window=50).mean()
        data['Long_MA'] = data['Close'].rolling(window=200).mean()
        golden_crosses = ((data['Short_MA'] > data['Long_MA']) & (data['Short_MA'].shift(1) <= data['Long_MA'].shift(1)))
        death_crosses = ((data['Short_MA'] < data['Long_MA']) & (data['Short_MA'].shift(1) >= data['Long_MA'].shift(1)))

        ax = plt.subplot(nrows, ncols, i + 1)
        ax.plot(data['Close'], label='Close Price', color='blue', alpha=0.6)
        ax.plot(data['Short_MA'], label='50-day MA', color='black', alpha=0.6)
        ax.plot(data['Long_MA'], label='200-day MA', color='magenta', alpha=0.6)
        ax.scatter(data.index[golden_crosses], data['Short_MA'][golden_crosses], color='gold', label='Golden Cross', marker='^', zorder=5)
        ax.scatter(data.index[death_crosses], data['Short_MA'][death_crosses], color='darkred', label='Death Cross', marker='v', zorder=5)
        ax.set_title(ticker)
        ax.set_xlabel('Date')
        ax.set_ylabel('Price')
        ax.legend()
        if y_min is not None:
            ax.set_ylim(bottom=y_min)

        # Check for a golden cross today
        today_golden_cross = 'Yes' if golden_crosses.iloc[-1] else 'No'
        email_details[ticker] = {
            'closing_price': data['Close'].iloc[-1],
            'golden_cross_today': today_golden_cross
        }

    plt.tight_layout()

    save_path = os.path.join("stock_analysis", f"{current_time}.png")
    os.makedirs("stock_analysis", exist_ok=True)
    plt.savefig(save_path)
    return save_path, email_details


def send_email_with_attachment(subject, attachment_path, sender_email, receiver_email, password, email_details, additional_email=None):
    msg = MIMEMultipart()
    msg['From'] = sender_email
    msg['To'] = receiver_email
    msg['Subject'] = subject

    # Prepare and attach the custom body
    body_content = ""
    golden_cross_flag = False
    for ticker, details in email_details.items():
        body_content += f"<b>{ticker}</b><br>Closing Price: {details['closing_price']:.2f}<br>Golden Cross Today: {details['golden_cross_today']}<br><br>"
        if details['golden_cross_today'] == 'Yes':
            golden_cross_flag = True  # Set flag if any golden cross is detected today
    
    msg.attach(MIMEText(body_content, 'html'))

    with open(attachment_path, 'rb') as attachment:
        part = MIMEBase('application', 'octet-stream')
        part.set_payload(attachment.read())
        encoders.encode_base64(part)
        part.add_header('Content-Disposition', f'attachment; filename={os.path.basename(attachment_path)}')
        msg.attach(part)

    # Send the email to the primary recipient
    try:
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(sender_email, password)
        text = msg.as_string()
        server.sendmail(sender_email, receiver_email, text)
        print("Email sent successfully to the primary recipient!")

        # If a golden cross is detected, send the email to the additional recipient
        if golden_cross_flag and additional_email:
            msg['To'] = additional_email
            text = msg.as_string()  # Update the text to reflect the new recipient
            server.sendmail(sender_email, additional_email, text)
            print("Email also sent to the additional recipient due to golden cross detection!")

    except Exception as e:
        print(f"Failed to send email: {e}")
    finally:
        server.quit()


# Execute functions and send email
save_path, email_details = fetch_and_visualize(tickers, years_back=years_back, y_min=y_min)
additional_email = config['email'].get('additional_email')  # Assuming you add this to your TOML file
send_email_with_attachment(subject, save_path, sender_email, receiver_email, password, email_details, additional_email)
