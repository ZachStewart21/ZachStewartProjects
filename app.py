import os
import yfinance as yf
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from flask import Flask, request, render_template

app = Flask(__name__, template_folder="templates")

def get_stock_data(ticker):
    stock = yf.Ticker(ticker)
    info = stock.info
    
    return {
        'current_price': info.get('currentPrice', None),
        'pe_ratio': info.get('trailingPE', None),
        'pb_ratio': info.get('priceToBook', None),
        'eps': info.get('trailingEps', None),
        'growth_rate': info.get('earningsGrowth', None),
        'beta': info.get('beta', None),
        'short_interest': info.get('shortPercentOfFloat', None),
        'institutional_shares': info.get('heldPercentInstitutions', None),
        'target_high': info.get('targetHighPrice', None),  # Institutional high target
        'target_low': info.get('targetLowPrice', None),    # Institutional low target
        'target_mean': info.get('targetMeanPrice', None)   # Institutional mean target
    }

import os
import matplotlib.pyplot as plt

def get_stock_chart(ticker):
    stock = yf.Ticker(ticker)
    df = stock.history(period="1y")

    if df.empty:
        return None

    df["50_MA"] = df["Close"].rolling(window=50).mean()
    df["200_MA"] = df["Close"].rolling(window=200).mean()

    # Ensure the static folder exists
    static_folder = "static"
    if not os.path.exists(static_folder):
        os.makedirs(static_folder)

    # Define chart path
    chart_path = os.path.join(static_folder, f"{ticker}_chart.png")

    # Create and save the chart
    plt.figure(figsize=(10, 5))
    plt.plot(df.index, df["Close"], label="Closing Price", color="blue")
    plt.plot(df.index, df["50_MA"], label="50-Day MA", color="orange")
    plt.plot(df.index, df["200_MA"], label="200-Day MA", color="red")
    
    plt.title(f"{ticker} Stock Price & Moving Averages")
    plt.xlabel("Date")
    plt.ylabel("Price (USD)")
    plt.legend()
    plt.grid(True)

    plt.savefig(chart_path)
    plt.close()

    return chart_path


@app.route("/", methods=["GET", "POST"])
def home():
    if request.method == "POST":
        ticker = request.form["ticker"].upper()
        data = get_stock_data(ticker)

        if data["current_price"] is None:
            return render_template("index.html", error="Stock data unavailable.", ticker=ticker)
        
        chart_path = get_stock_chart(ticker)

        return render_template("index.html", data=data, ticker=ticker, chart_path=chart_path)

    return render_template("index.html")

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))  # Ensure Flask runs on the correct port in Render
    app.run(host="0.0.0.0", port=port, debug=True)

