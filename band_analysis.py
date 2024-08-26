import yfinance as yf
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import pytz
import toml
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
import os

# Load settings from the TOML file
config = toml.load("settings.toml")
tickers = config['tickers']['symbols']
years_back = config['analysis']['years_back']
y_min = config['analysis']['y_min']
ma_period = config['analysis']['ma_period']

# Email settings
sender_email = config['email']['sender_email']
receiver_email = config['email']['receiver_email']
password = config['email']['password']
body = config['email']['body']

timezone = pytz.timezone('Australia/Perth')

# Get current time in the specified timezone
current_time = datetime.now(timezone).strftime("%Y%m%d_%H%M%S")

# Update the subject to include the date and time
subject = f"{datetime.now().strftime('%d/%m/%Y')} - Auto Stock Report"


def fetch_and_visualize(tickers, years_back=5, ma_period=100, y_min=None):
    # Determine subplot dimensions
    nrows = 2  # Arrange plots in two columns
    ncols = 3
    email_details = {}
    
    plt.figure(figsize=(15, 5 * nrows))  # Adjust overall figure size

    for i, ticker in enumerate(tickers):
        # Set current date as end date and calculate start date
        end_date = datetime.now()
        start_date = end_date - timedelta(days=365 * years_back)
        
        # Format dates for yfinance
        end_date = end_date.strftime('%Y-%m-%d')
        start_date = start_date.strftime('%Y-%m-%d')
        
        # Fetch historical stock data
        data = yf.download(ticker, start=start_date, end=end_date)
        
        # Calculate moving averages for Bollinger Bands and Golden/Death Crosses
        data['MA'] = data['Close'].rolling(window=ma_period).mean()
        #data['STD'] = data['Close'].rolling(window=ma_period).std()
        #data['Upper'] = data['MA'] + (data['STD'] * 2)
        #data['Lower'] = data['MA'] - (data['STD'] * 2)
        data['Short_MA'] = data['Close'].rolling(window=50).mean()  # 50-day MA
        data['Long_MA'] = data['Close'].rolling(window=200).mean()  # 200-day MA

        # Identify golden and death crosses
        golden_crosses = ((data['Short_MA'] > data['Long_MA']) & (data['Short_MA'].shift(1) <= data['Long_MA'].shift(1)))
        death_crosses = ((data['Short_MA'] < data['Long_MA']) & (data['Short_MA'].shift(1) >= data['Long_MA'].shift(1)))

        # Subplot for each ticker
        ax = plt.subplot(nrows, ncols, i + 1)
        
        # Plotting the stock prices, Bollinger Bands, and moving averages
        ax.plot(data['Close'], label='Close Price', color='blue', alpha=0.5)
        #ax.plot(data['Upper'], label='Upper Band', color='green')
        #ax.plot(data['Lower'], label='Lower Band', color='red')
        ax.plot(data['Short_MA'], label='50-day MA', color='orange')
        ax.plot(data['Long_MA'], label='200-day MA', color='black')
        
        """
        # Draw shaded vertical strips at each below-lower-band region
        start_date = None
        below_lower = data['Close'] < data['Lower']
        for date, is_below in zip(data.index, below_lower):
            if is_below and start_date is None:
                start_date = date
            elif not is_below and start_date is not None:
                ax.axvspan(start_date, date, color='magenta', alpha=0.3)
                start_date = None
        if start_date is not None:
            ax.axvspan(start_date, data.index[-1], color='magenta', alpha=0.3)
            
            
        # Draw shaded vertical strips at each above-upper-band region
        start_date = None
        above_upper = data['Close'] > data['Upper']
        for date, is_above in zip(data.index, above_upper):
            if is_above and start_date is None:
                start_date = date
            elif not is_above and start_date is not None:
                ax.axvspan(start_date, date, color='green', alpha=0.3)
                start_date = None
        if start_date is not None:
            ax.axvspan(start_date, data.index[-1], color='green', alpha=0.3)
        """
            
        # Mark the golden and death crosses
        ax.scatter(data.index[golden_crosses], data['Short_MA'][golden_crosses], color='gold', label='Golden Cross', marker='^', zorder=5)
        ax.scatter(data.index[death_crosses], data['Short_MA'][death_crosses], color='darkred', label='Death Cross', marker='v', zorder=5)

        # Title, labels, and legend for subplot
        ax.set_title(f'{ticker}')
        ax.set_xlabel('Date')
        ax.set_ylabel('Price')
        ax.legend()

        # Set the minimum y-axis value if specified
        if y_min is not None:
            ax.set_ylim(bottom=y_min)

        """# Add stock details for email
        email_details[ticker] = {
            'closing_price': data['Close'].iloc[-1],
            'below_lower_band': 'Under the lower band' if below_lower.iloc[-1] else 'Above the lower band'
        }"""

    plt.tight_layout()
    plt.show()
    
    # Save the figure
    save_path = os.path.join("stock_analysis", f"{current_time}.png")
    os.makedirs("stock_analysis", exist_ok=True)
    plt.savefig(save_path)

    return save_path, email_details



def send_email_with_attachment(subject, attachment_path, sender_email, receiver_email, password, email_details):
    msg = MIMEMultipart()
    msg['From'] = sender_email
    msg['To'] = receiver_email
    msg['Subject'] = subject

    # Prepare and attach the custom body
    body_content = ""
    for ticker, details in email_details.items():
        body_content += f"<b>{ticker}</b><br>Closing Price: {details['closing_price']:.2f}<br>{details['below_lower_band']}<br><br>"
    msg.attach(MIMEText(body_content, 'html'))

    with open(attachment_path, 'rb') as attachment:
        part = MIMEBase('application', 'octet-stream')
        part.set_payload(attachment.read())
        encoders.encode_base64(part)
        part.add_header('Content-Disposition', f'attachment; filename={os.path.basename(attachment_path)}')
        msg.attach(part)

    try:
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(sender_email, password)
        text = msg.as_string()
        server.sendmail(sender_email, receiver_email, text)
        print("Email sent successfully!")
    except Exception as e:
        print(f"Failed to send email: {e}")
    finally:
        server.quit()

# Execute functions and send email
save_path, email_details = fetch_and_visualize(tickers, years_back=years_back, ma_period=ma_period, y_min=y_min)
#send_email_with_attachment(subject, save_path, sender_email, receiver_email, password, email_details)