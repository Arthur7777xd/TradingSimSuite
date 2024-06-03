"""
Portfolio Manager for Financial Portfolio

This module contains functions to load, save, and manage a financial portfolio.
It uses `yfinance` to fetch financial data and `pandas` for data processing.

Installation:
    pip install yfinance pandas

Author: Arthur Simon, MNr: 9227155
Date: 02.06.2024
license: free
version: 0.0.1 (master.major.minor)
"""

import json
import os
import yfinance as yf
from fastapi import HTTPException


def load_portfolio() -> tuple:
    """
    Load the portfolio from a JSON file or initialize with default values.

    Returns:
        tuple: The starting capital (int) and the portfolio dictionary (dict). -> (int, dict)

    Tests:
        1. Test loading a valid portfolio from a file to verify it loads correctly.
        2. Test with a missing or corrupted file to verify it initializes with default values.
    """
    default_capital = 1000000
    default_portfolio = {}

    if os.path.exists("portfolio.json"):
        try:
            with open("portfolio.json", "r") as f:
                saved_data = json.load(f)
                start_capital = saved_data.get("start_capital", default_capital)
                portfolio = saved_data.get("portfolio", default_portfolio)
        except (json.JSONDecodeError, FileNotFoundError):
            start_capital = default_capital
            portfolio = default_portfolio
            save_portfolio(start_capital, portfolio)
    else:
        start_capital = default_capital
        portfolio = default_portfolio
        save_portfolio(start_capital, portfolio)

    return start_capital, portfolio


def save_portfolio(start_capital: int, portfolio: dict) -> None:
    """
    Save the portfolio to a JSON file.

    Args:
        start_capital (int): The starting capital.
        portfolio (dict): The portfolio dictionary.

    Returns:
        None -> None

    Tests:
        1. Test saving a valid portfolio to verify it writes the data correctly.
        2. Test saving with different data structures to verify it handles various edge cases.
    """
    with open("portfolio.json", "w") as f:
        json.dump({"start_capital": start_capital, "portfolio": portfolio}, f)


def fetch_portfolio_data(portfolio: dict) -> None:
    """
    Fetch data for all tickers in the portfolio and save it as CSV files.

    Args:
        portfolio (dict): The portfolio dictionary.

    Returns:
        None -> None

    Tests:
        1. Test with a valid portfolio to verify it fetches and saves data correctly.
        2. Test with an empty portfolio to verify it handles edge cases.
    """
    if not os.path.exists("data"):
        os.makedirs("data")

    for ticker in portfolio.keys():
        file_path = f"data/{ticker}.csv"
        if not os.path.exists(file_path):
            data = yf.download(ticker)
            if not data.empty:
                data.to_csv(file_path)


def get_current_portfolio_value(portfolio: dict) -> float:
    """
    Calculate the current total value of the portfolio.

    Args:
        portfolio (dict): The portfolio dictionary.

    Returns:
        float: The total value of the portfolio. -> float

    Raises:
        HTTPException: If any ticker data is not found.

    Tests:
        1. Test with a valid portfolio to verify it calculates the value correctly.
        2. Test with an invalid ticker in the portfolio to verify it raises a 404 HTTPException.
    """
    total_value = 0
    for ticker, quantity in portfolio.items():
        data = yf.download(ticker, period="1d", interval="1m")
        if data.empty:
            raise HTTPException(status_code=404, detail=f"Ticker {ticker} not found")
        current_price = data["Close"].iloc[-1]
        total_value += current_price * quantity
    return total_value
