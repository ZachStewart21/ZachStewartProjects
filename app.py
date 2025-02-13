from flask import Flask, request, render_template
import yfinance as yf
import numpy as np

app = Flask(__name__)

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
        'institutional_shares': info.get('heldPercentInstitutions', None)
    }

def dcf_valuation(eps, growth_rate, discount_rate=0.1, years=10):
    if eps is None or growth_rate is None:
        return None
    future_cashflows = [(eps * (1 + growth_rate) ** i) / (1 + discount_rate) ** i for i in range(1, years + 1)]
    terminal_value = (future_cashflows[-1] * (1 + growth_rate)) / (discount_rate - growth_rate)
    intrinsic_value = sum(future_cashflows) + terminal_value
    return intrinsic_value

@app.route("/", methods=["GET", "POST"])
def home():
    if request.method == "POST":
        ticker = request.form["ticker"].upper()
        data = get_stock_data(ticker)
        
        if data["current_price"] is None:
            return render_template("index.html", error="Stock data unavailable.", ticker=ticker)
        
        dcf_value = dcf_valuation(data["eps"], data["growth_rate"])
        
        valuation_metrics = {
            "P/E Ratio": data["pe_ratio"],
            "P/B Ratio": data["pb_ratio"],
            "Beta": data["beta"],
            "Short Interest (%)": data["short_interest"] * 100 if data["short_interest"] is not None else None,
            "Institutional Ownership (%)": data["institutional_shares"] * 100 if data["institutional_shares"] is not None else None,
            "DCF Fair Value": dcf_value,
            "Current Price": data["current_price"]
        }

        # Generate recommendation based on DCF valuation
        if dcf_value and dcf_value > data["current_price"] * 1.2:
            recommendation = "BUY (Undervalued)"
        elif dcf_value and dcf_value < data["current_price"] * 0.8:
            recommendation = "SELL (Overvalued)"
        else:
            recommendation = "HOLD (Fairly Valued)"

        return render_template("index.html", data=valuation_metrics, recommendation=recommendation, ticker=ticker)

    return render_template("index.html")

if __name__ == "__main__":
    app.run(debug=True)
