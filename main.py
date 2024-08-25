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


def fetch_dividend_yield(ticker, years_back=5):
    # Set current date as end date and calculate start date
    end_date = datetime.now()
    start_date = end_date - timedelta(days=365 * years_back)
    
    # Format dates for yfinance
    end_date = end_date.strftime('%Y-%m-%d')
    start_date = start_date.strftime('%Y-%m-%d')
    
    # Fetch historical stock data
    stock = yf.Ticker(ticker)
    dividends = stock.dividends
    prices = stock.history(start=start_date, end=end_date)['Close']

    # Filter dividends within the period
    dividends = dividends[(dividends.index >= start_date) & (dividends.index <= end_date)]
    
    # Calculate dividend yield on each dividend date
    dividend_yields = []
    for date, dividend in dividends.items():
        # Get the closing price on the day before the dividend was paid
        price = prices.loc[prices.index <= date].iloc[-1]
        yield_value = dividend / price
        dividend_yields.append(yield_value)
    
    # Calculate the average dividend yield over the period
    if dividend_yields:
        average_yield = np.mean(dividend_yields) * 100  # Convert to percentage
    else:
        average_yield = 0  # No dividends in this period

    return average_yield

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
        
        # Calculate the moving average and the standard deviation
        data['MA'] = data['Close'].rolling(window=ma_period).mean()
        data['STD'] = data['Close'].rolling(window=ma_period).std()
        
        # Calculate Bollinger Bands
        data['Upper'] = data['MA'] + (data['STD'] * 2)
        data['Lower'] = data['MA'] - (data['STD'] * 2)

        # Subplot for each ticker
        ax = plt.subplot(nrows, ncols, i + 1)
        
        # Plotting the stock prices and Bollinger Bands
        ax.plot(data['Close'], label='Close Price', color='blue')
        ax.plot(data['Upper'], label='Upper Band', color='green')
        ax.plot(data['Lower'], label='Lower Band', color='red')
        
        # Highlight where close is below the lower Bollinger Band
        below_lower = data['Close'] < data['Lower']
        ax.fill_between(data.index, data['Lower'], data['Close'], where=below_lower, color='red', alpha=0.3, label='Below Lower Band')
        
        # Draw shaded vertical strips at each below-lower-band region
        start_date = None
        for date, is_below in zip(data.index, below_lower):
            if is_below and start_date is None:
                start_date = date
            elif not is_below and start_date is not None:
                ax.axvspan(start_date, date, color='magenta', alpha=0.3)
                start_date = None
        if start_date is not None:
            ax.axvspan(start_date, data.index[-1], color='magenta', alpha=0.3)

        # Add a linear trend line
        z = np.polyfit(range(len(data['Close'])), data['Close'], 1)
        p = np.poly1d(z)
        ax.plot(data.index, p(range(len(data['Close']))), "r--", label='Trend Line')

        # Calculate CAGR based on trendline values
        if len(data['Close']) > 0:
            start_price = p(0)  # Start value on the trendline
            end_price = p(len(data['Close']) - 1)  # End value on the trendline
            years = years_back
            CAGR = ((end_price / start_price) ** (1 / years) - 1) * 100
        
        # Calculate average dividend yield
        average_dividend_yield = fetch_dividend_yield(ticker, years_back=years_back)

        # Title and labels for subplot
        current_condition = "Below" if below_lower.iloc[-1] else "Above"
        ax.set_title(f'{ticker} - {current_condition} Lower Band\nYoY Growth: {CAGR:.2f}%, Avg Div Yield: {average_dividend_yield:.2f}%')
        ax.set_xlabel('Date')
        ax.set_ylabel('Price')

        # Set the minimum y-axis value if specified
        if y_min is not None:
            ax.set_ylim(bottom=y_min)

        ax.legend()
        
        # Add stock details for email
        email_details[ticker] = {
            'closing_price': data['Close'].iloc[-1],
            'below_lower_band': 'Under the lower band' if below_lower.iloc[-1] else 'Above the lower band'
        }

    plt.tight_layout()
    
    # Use os.path.join to create a path that works on all operating systems
    save_path = os.path.join("stock_analysis", f"{current_time}.png")
    
    # Ensure the directory exists before saving
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
send_email_with_attachment(subject, save_path, sender_email, receiver_email, password, email_details)