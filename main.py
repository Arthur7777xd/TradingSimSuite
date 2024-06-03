"""
FastAPI Backend for Portfolio Management

This module implements a backend for a portfolio management system using FastAPI.
It uses `yfinance` to fetch financial data and `pandas` for data processing.

Installation:
    pip install fastapi uvicorn yfinance pandas

Author: Arthur Simon, MNr: 9227155
Date: 02.06.2024
license: free
version: 0.0.1 (master.major.minor)
"""

from fastapi import FastAPI, HTTPException, Query
import yfinance as yf
import pandas as pd
import os
from portfolio_manager import (
    load_portfolio,
    save_portfolio,
    get_current_portfolio_value,
    fetch_portfolio_data,
)

app = FastAPI()

start_capital, portfolio = load_portfolio()

# Fetch data for all tickers in the portfolio on startup
fetch_portfolio_data(portfolio)


@app.get("/search/{query}")
def search_symbol(query: str) -> dict:
    """
    Search for a stock symbol and return its details.

    Args:
        query (str): The stock symbol to search for.

    Returns:
        dict: A dictionary with the symbol and name of the stock. -> {"symbol": str, "name": str}

    Raises:
        HTTPException: If no data is found for the query or an internal error occurs.

    Tests:
        1. Test with a valid stock symbol (e.g., "AAPL") to verify it returns the correct details.
        2. Test with an invalid stock symbol (e.g., "INVALID") to verify it raises a 404 HTTPException.
    """
    try:
        result = yf.Ticker(query.upper()).info
        if not result:
            raise HTTPException(status_code=404, detail="No data found for query")
        return {"symbol": result.get("symbol"), "name": result.get("shortName")}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/historical-data/{ticker}")
def get_historical_data(
    ticker: str,
    period: str = Query(
        "1y", pattern="^(1d|5d|1mo|3mo|6mo|1y|2y|5y|10y|ytd|max)$"
    ),
) -> dict:
    """
    Get historical data for a given stock ticker and save it as a CSV file.

    Args:
        ticker (str): The stock ticker to fetch data for.
        period (str): The period for which to fetch data (default is "1y").

    Returns:
        dict: A message indicating the file path where the data was saved. -> {"message": str}

    Raises:
        HTTPException: If no data is found for the ticker or an internal error occurs.

    Tests:
        1. Test with a valid ticker (e.g., "AAPL") and period to verify it saves the data correctly.
        2. Test with an invalid ticker (e.g., "INVALID") to verify it raises a 404 HTTPException.
    """
    try:
        data = yf.download(ticker.upper(), period=period)
        if data.empty:
            raise HTTPException(status_code=404, detail="No data found for ticker")

        file_path = f"data/{ticker.upper()}.csv"
        data.to_csv(file_path)
        return {"message": f"Data saved to {file_path}"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/buy")
def buy_stock(ticker: str, quantity: int) -> dict:
    """
    Buy a specified quantity of a stock.

    Args:
        ticker (str): The stock ticker to buy.
        quantity (int): The quantity of shares to buy.

    Returns:
        dict: A message indicating the purchase details, remaining capital, total portfolio value, and updated portfolio. -> {"message": str, "remaining_capital": float, "total_value": float, "portfolio": dict}

    Raises:
        HTTPException: If historical data is not fetched, ticker not found, or insufficient funds.

    Tests:
        1. Test buying a valid stock (e.g., "AAPL") with sufficient funds to verify the purchase is successful.
        2. Test buying a stock (e.g., "AAPL") with insufficient funds to verify it raises a 400 HTTPException.
    """
    global start_capital, portfolio
    ticker = ticker.upper()
    file_path = f"data/{ticker}.csv"

    if not os.path.exists(file_path):
        raise HTTPException(
            status_code=400,
            detail="Please fetch the historical data for this ticker before making a purchase.",
        )

    data = pd.read_csv(file_path)
    if data.empty:
        raise HTTPException(status_code=404, detail="Ticker not found")

    current_price = data["Close"].iloc[-1]
    total_cost = current_price * quantity

    if total_cost > start_capital:
        raise HTTPException(status_code=400, detail="Insufficient funds")

    start_capital -= total_cost
    portfolio[ticker] = portfolio.get(ticker, 0) + quantity
    save_portfolio(start_capital, portfolio)

    total_value = get_current_portfolio_value(portfolio)

    return {
        "message": f"Bought {quantity} shares of {ticker}",
        "remaining_capital": start_capital,
        "total_value": total_value,
        "portfolio": portfolio,
    }


@app.post("/sell")
def sell_stock(ticker: str, quantity: int) -> dict:
    """
    Sell a specified quantity of a stock.

    Args:
        ticker (str): The stock ticker to sell.
        quantity (int): The quantity of shares to sell.

    Returns:
        dict: A message indicating the sale details, remaining capital, total portfolio value, and updated portfolio. -> {"message": str, "remaining_capital": float, "total_value": float, "portfolio": dict}

    Raises:
        HTTPException: If the ticker is not in the portfolio or there are insufficient shares.

    Tests:
        1. Test selling a valid stock (e.g., "AAPL") with sufficient shares to verify the sale is successful.
        2. Test selling a stock (e.g., "AAPL") with insufficient shares to verify it raises a 400 HTTPException.
    """
    global start_capital, portfolio
    ticker = ticker.upper()
    if ticker not in portfolio or portfolio[ticker] < quantity:
        raise HTTPException(status_code=400, detail="Insufficient shares")

    data = yf.download(ticker)
    current_price = data["Close"].iloc[-1]
    total_revenue = current_price * quantity

    start_capital += total_revenue
    portfolio[ticker] -= quantity

    if portfolio[ticker] == 0:
        del portfolio[ticker]

    save_portfolio(start_capital, portfolio)

    total_value = get_current_portfolio_value(portfolio)

    return {
        "message": f"Sold {quantity} shares of {ticker}",
        "remaining_capital": start_capital,
        "total_value": total_value,
        "portfolio": portfolio,
    }


@app.get("/portfolio")
def get_portfolio() -> dict:
    """
    Get the current portfolio details.

    Returns:
        dict: The current portfolio and remaining capital. -> {"portfolio": dict, "remaining_capital": float}

    Tests:
        1. Test retrieving the portfolio when it has stocks to verify it returns the correct details.
        2. Test retrieving the portfolio when it is empty to verify it returns the correct details.
    """
    return {"portfolio": portfolio, "remaining_capital": start_capital}


@app.get("/portfolio-value")
def get_portfolio_value() -> dict:
    """
    Get the current total value of the portfolio.

    Returns:
        dict: The total value of the portfolio. -> {"total_value": float}

    Raises:
        HTTPException: If there is an error fetching the portfolio value.

    Tests:
        1. Test retrieving the portfolio value with a valid portfolio to verify it returns the correct value.
        2. Test retrieving the portfolio value with an empty portfolio to verify it returns 0 or an appropriate value.
    """
    try:
        total_value = get_current_portfolio_value(portfolio)
        return {"total_value": total_value}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
