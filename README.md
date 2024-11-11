# Gruppe Trading Snake
## Author: Arthur Simon, MNr: -

# README for Trading Simulator Application
Overview

This application is a trading simulator that allows users to manage a financial portfolio through a graphical user interface (GUI) built with Tkinter. The backend of the application is powered by FastAPI, which handles requests to fetch stock data using the yfinance library and processes data with pandas.

How the Program Works
## Backend

The backend is built using FastAPI and provides several endpoints to handle portfolio management tasks:

    Search Symbol: Searches for a stock symbol and returns its details.
    Get Historical Data: Fetches historical data for a given stock ticker and saves it as a CSV file.
    Buy Stock: Buys a specified quantity of a stock and updates the portfolio.
    Sell Stock: Sells a specified quantity of a stock and updates the portfolio.
    Get Portfolio: Retrieves the current portfolio details.
    Get Portfolio Value: Retrieves the total value of the portfolio.

The backend uses the yfinance library to fetch stock data and pandas for data processing.
## Frontend

The frontend is a Tkinter-based GUI that allows users to interact with their portfolio. Users can:

    Enter a stock or cryptocurrency symbol to search for it.
    Select a time period to fetch and display historical data.
    Buy or sell stocks and update their portfolio.
    View the current portfolio holdings and their value over time.

The frontend interacts with the backend through HTTP requests to fetch data and perform transactions.
Note

There is no web crawler in the application. Initially, an API that required crawling was chosen, but it did not fit within the project's timeline, leading to a change in approach.

The portfolio value is updated every minute because the API enables 1 Minute as minimum interval.
