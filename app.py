import os
import yfinance as yf
import numpy as np
import pandas as pd
import plotly.graph_objects as go
from flask import Flask, request, render_template

app = Flask(__name__, template_folder="templates")

def get_stock_data(ticker, strategy):
    stock = yf.Ticker(ticker)
    info = stock.info
    history = stock.history(period="1y")

    if not history.empty:
        history["Daily Return"] = history["Close"].pct_change()
        expected_return = history["Daily Return"].mean() * 252
        risk = history["Daily Return"].std() * np.sqrt(252)
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
        'expected_return': expected_return,
        'risk': risk
    }

    data['recommendation'] = get_recommendation(data, strategy)

    return data

def get_recommendation(data, strategy):
    eps = data['eps']
    short_interest = data['short_interest']
    beta = data['beta']
    current_price = data['current_price']
    target_mean = data['target_mean']
    target_high = data['target_high']

    if None in (eps, short_interest, beta, current_price, target_mean, target_high):
        return "Insufficient Data for Recommendation"

    if strategy == "risk_averse":
        beta_threshold = 1.0
        short_interest_threshold = 0.10
    elif strategy == "moderate":
        beta_threshold = 1.2
        short_interest_threshold = 0.20
    elif strategy == "high_risk":
        beta_threshold = 1.5
        short_interest_threshold = 0.30
    else:
        beta_threshold = 1.2
        short_interest_threshold = 0.20

    if short_interest < short_interest_threshold and eps > 0.1 and beta <= beta_threshold and current_price < target_mean:
        return f"BUY - Aligned with {strategy.replace('_', ' ').title()} strategy."

    if short_interest > short_interest_threshold * 1.5 or eps < 0 or beta > beta_threshold + 0.5 or current_price > target_high:
        return f"SELL - Too risky for {strategy.replace('_', ' ').title()} strategy."

    return f"HOLD - No strong buy/sell signal for {strategy.replace('_', ' ').title()} strategy."

def get_stock_chart(ticker, time_range="6mo", ma_list=[50]):
    stock = yf.Ticker(ticker)
    df = stock.history(period=time_range)

    if df.empty:
        return None

    fig = go.Figure()

    fig.add_trace(go.Candlestick(
        x=df.index,
        open=df['Open'],
        high=df['High'],
        low=df['Low'],
        close=df['Close'],
        name='Candlestick'
    ))

    for ma in ma_list:
        df[f"MA{ma}"] = df["Close"].rolling(window=ma).mean()
        fig.add_trace(go.Scatter(
            x=df.index,
            y=df[f"MA{ma}"],
            mode="lines",
            name=f"{ma}-Day MA"
        ))

    fig.update_layout(
        title=f"{ticker} - {time_range.upper()} Candlestick Chart",
        xaxis_title="Date",
        yaxis_title="Price (USD)",
        template="plotly_white",
        xaxis_rangeslider_visible=False,
        height=600
    )

    return fig.to_html(full_html=False)

@app.route("/", methods=["GET", "POST"])
def home():
    if request.method == "POST":
        ticker = request.form["ticker"].upper()
        strategy = request.form["strategy"]
        time_range = request.form.get("range", "6mo")
        ma_values = request.form.getlist("ma")
        ma_values = [int(ma) for ma in ma_values if ma.isdigit()]

        data = get_stock_data(ticker, strategy)

        if data["current_price"] is None:
            return render_template("index.html", error="Stock data unavailable.", ticker=ticker)

        chart_html = get_stock_chart(ticker, time_range, ma_values)

        return render_template("index.html", data=data, ticker=ticker, chart_html=chart_html, strategy=strategy)

    return render_template("index.html")

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
