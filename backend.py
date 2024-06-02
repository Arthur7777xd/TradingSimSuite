# main.py

from fastapi import FastAPI, HTTPException, Query
import yfinance as yf
import os
import json
import pandas as pd

app = FastAPI()

# Load start capital from config file
with open('config.json', 'r') as f:
    config = json.load(f)

start_capital = config['start_capital']
portfolio = {}

# Ensure 'data' directory exists
if not os.path.exists('data'):
    os.makedirs('data')


@app.get("/search/{query}")
def search_symbol(query: str):
    try:
        result = yf.Ticker(query).info
        if not result:
            raise HTTPException(status_code=404, detail="No data found for query")
        
        return {"symbol": result.get("symbol"), "name": result.get("shortName")}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/historical-data/{ticker}")
def get_historical_data(ticker: str, period: str = Query("1y", pattern="^(1d|5d|1mo|3mo|6mo|1y|2y|5y|10y|ytd|max)$")):
    try:
        data = yf.download(ticker, period=period)
        if data.empty:
            raise HTTPException(status_code=404, detail="No data found for ticker")
        
        file_path = f"data/{ticker}.csv"
        data.to_csv(file_path)
        return {"message": f"Data saved to {file_path}"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/buy")
def buy_stock(ticker: str, quantity: int):
    global start_capital, portfolio
    data = yf.download(ticker)
    if data.empty:
        raise HTTPException(status_code=404, detail="Ticker not found")

    current_price = data['Close'].iloc[-1]
    total_cost = current_price * quantity

    if total_cost > start_capital:
        raise HTTPException(status_code=400, detail="Insufficient funds")

    start_capital -= total_cost
    if ticker in portfolio:
        portfolio[ticker] += quantity
    else:
        portfolio[ticker] = quantity

    return {"message": f"Bought {quantity} shares of {ticker}", "remaining_capital": start_capital}


@app.post("/sell")
def sell_stock(ticker: str, quantity: int):
    global start_capital, portfolio
    if ticker not in portfolio or portfolio[ticker] < quantity:
        raise HTTPException(status_code=400, detail="Insufficient shares")

    data = yf.download(ticker)
    current_price = data['Close'].iloc[-1]
    total_revenue = current_price * quantity

    start_capital += total_revenue
    portfolio[ticker] -= quantity

    if portfolio[ticker] == 0:
        del portfolio[ticker]

    return {"message": f"Sold {quantity} shares of {ticker}", "remaining_capital": start_capital}


@app.get("/portfolio")
def get_portfolio():
    return {"portfolio": portfolio, "remaining_capital": start_capital}


@app.get("/current-price/{ticker}")
def get_current_price(ticker: str):
    try:
        data = yf.download(ticker, period="1d", interval="1m")
        if data.empty:
            raise HTTPException(status_code=404, detail="Ticker not found")
        current_price = data['Close'].iloc[-1]
        return {"ticker": ticker, "current_price": current_price}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/portfolio-value")
def get_portfolio_value():
    try:
        tickers = list(portfolio.keys())
        if not tickers:
            return {"total_value": 0}

        total_value = 0

        for ticker in tickers:
            data = yf.download(ticker, period="1d", interval="1m")
            if data.empty:
                raise HTTPException(status_code=404, detail=f"Ticker {ticker} not found")
            current_price = data['Close'].iloc[-1]
            total_value += current_price * portfolio[ticker]

        return {"total_value": total_value}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)