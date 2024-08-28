import numpy as np
from datetime import datetime, timedelta
import pytz
import yfinance as yf
import matplotlib.pyplot as plt
import os
import toml
from send_email import send_email_with_attachment

# Load settings from the TOML file
config = toml.load("settings.toml")
tickers = config['tickers']['symbols']
years_back = config['analysis']['years_back']
y_min = None

# Email settings
sender_email = config['email']['sender_email']
receiver_email = config['email']['receiver_email']
password = config['email']['password']
body = ""

timezone = pytz.timezone('Australia/Perth')
current_time = datetime.now(timezone).strftime("%Y%m%d_%H%M%S")
subject = f"{datetime.now().strftime('%d/%m/%Y')} - Auto Stock Report"

def fetch_dividend_yield(ticker, years_back=5):
    end_date = datetime.now()
    start_date = end_date - timedelta(days=365 * years_back)
    end_date = end_date.strftime('%Y-%m-%d')
    start_date = start_date.strftime('%Y-%m-%d')
    stock = yf.Ticker(ticker)
    dividends = stock.dividends
    prices = stock.history(start=start_date, end=end_date)['Close']
    dividends = dividends[(dividends.index >= start_date) & (dividends.index <= end_date)]
    
    dividend_yields = []
    for date, dividend in dividends.items():
        price = prices.loc[prices.index <= date].iloc[-1]
        yield_value = dividend / price
        dividend_yields.append(yield_value)
    
    if dividend_yields:
        average_yield = np.mean(dividend_yields) * 100  # Convert to percentage
    else:
        average_yield = 0
    return average_yield

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

        z = np.polyfit(range(len(data['Close'])), data['Close'], 1)
        p = np.poly1d(z)

        if len(data['Close']) > 0:
            start_price = p(0)
            end_price = p(len(data['Close']) - 1)
            years = years_back
            CAGR = ((end_price / start_price) ** (1 / years) - 1) * 100
        
        average_dividend_yield = fetch_dividend_yield(ticker, years_back=years_back)

        ax = plt.subplot(nrows, ncols, i + 1)
        ax.plot(data.index, p(range(len(data['Close']))), "r--", label='Trend Line')
        ax.plot(data['Close'], label='Close Price', color='blue', alpha=0.6)
        ax.plot(data['Short_MA'], label='50-day MA', color='black', alpha=0.6)
        ax.plot(data['Long_MA'], label='200-day MA', color='magenta', alpha=0.6)
        ax.scatter(data.index[golden_crosses], data['Short_MA'][golden_crosses], color='gold', label='Golden Cross', marker='^', zorder=5)
        ax.scatter(data.index[death_crosses], data['Short_MA'][death_crosses], color='darkred', label='Death Cross', marker='v', zorder=5)
        ax.set_title(f'{ticker}\nYoY Growth: {CAGR:.2f}%, Avg Div Yield: {average_dividend_yield:.2f}%')
        ax.set_xlabel('Date')
        ax.set_ylabel('Price')
        ax.legend()
        if y_min is not None:
            ax.set_ylim(bottom=y_min)

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

def format_email_body(email_details):
    body_content = ""
    for ticker, details in email_details.items():
        body_content += f"<b>{ticker}</b><br>Closing Price: {details['closing_price']:.2f}<br>Golden Cross Today: {details['golden_cross_today']}<br><br>"
    return body_content

# Execute functions and send email
save_path, email_details = fetch_and_visualize(tickers, years_back=years_back, y_min=y_min)
email_body = format_email_body(email_details)
send_email_with_attachment(subject, sender_email, receiver_email, password, email_body, attachment_path=save_path)
