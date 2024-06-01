# backend/api.py

from fastapi import FastAPI, HTTPException
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
def get_historical_data(ticker: str):
    try:
        data = yf.download(ticker, period="1y")
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

    current_price = data['Close'][-1]
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
    current_price = data['Close'][-1]
    total_revenue = current_price * quantity

    start_capital += total_revenue
    portfolio[ticker] -= quantity

    if portfolio[ticker] == 0:
        del portfolio[ticker]

    return {"message": f"Sold {quantity} shares of {ticker}", "remaining_capital": start_capital}

@app.get("/portfolio")
def get_portfolio():
    return {"portfolio": portfolio, "remaining_capital": start_capital}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
