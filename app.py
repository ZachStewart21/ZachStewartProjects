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
    history = stock.history(period="1y")  # <--- Pull historical prices here

    if not history.empty:
        history["Daily Return"] = history["Close"].pct_change()
        expected_return = history["Daily Return"].mean() * 252  # Annualized expected return
        risk = history["Daily Return"].std() * np.sqrt(252)     # Annualized volatility
    else:
        expected_return = None
        risk = None

    data = {
        'current_price': info.get('currentPrice', None),
        'pe_ratio': info.get('trailingPE', None),
        'pb_ratio': info.get('priceToBook', None),
        'eps': info.get('trailingEps', None),
        'growth_rate': info.get('earningsGrowth', None),
        'beta': info.get('beta', None),
        'short_interest': info.get('shortPercentOfFloat', None),
        'institutional_shares': info.get('heldPercentInstitutions', None),
        'target_high': info.get('targetHighPrice', None),  
        'target_low': info.get('targetLowPrice', None),    
        'target_mean': info.get('targetMeanPrice', None),
        'expected_return': expected_return,    # <<< New
        'risk': risk                           # <<< New
    }
    
    data['recommendation'] = get_recommendation(data)

    return data


def get_recommendation(data):
    """Determine Buy/Hold/Sell recommendation for a moderately aggressive investor."""
    eps = data['eps']
    short_interest = data['short_interest']
    beta = data['beta']
    current_price = data['current_price']
    target_mean = data['target_mean']
    target_high = data['target_high']

    if None in (eps, short_interest, beta, current_price, target_mean, target_high):
        return "Insufficient Data for Recommendation"

    # Buy Condition: Low P/E, positive growth, moderate to high risk, undervalued
    if short_interest < .10 and eps > 0.1 and beta > 1.0 and current_price < target_mean:
        return "BUY - Strong fundamentals with growth potential and moderate risk."

    # Hold Condition: Fair valuation, moderate growth, stable beta, fairly priced
    if .1 <= short_interest <= .25 and 0 <= eps <= 0.1 and 0.8 <= beta <= 1.2:
        return "HOLD - Stock is fairly valued with stable outlook."

    # Sell Condition: Overvalued, weak growth, excessive volatility
    if short_interest > .25 or eps < 0 or beta > 1.5 or current_price > target_high:
        return "SELL - Overvalued or declining fundamentals."

    return "HOLD - No strong buy or sell signal."


def get_stock_chart(ticker):
    stock = yf.Ticker(ticker)
    df = stock.history(period="1y")

    if df.empty:
        return None

    df["50_MA"] = df["Close"].rolling(window=50).mean()
    df["200_MA"] = df["Close"].rolling(window=200).mean()

    static_folder = "static"
    if not os.path.exists(static_folder):
        os.makedirs(static_folder)

    chart_path = os.path.join(static_folder, f"{ticker}_chart.png")

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
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
