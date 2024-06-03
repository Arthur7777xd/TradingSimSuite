"""
Trading Utilities Module
------------------------
This module provides utility functions for plotting historical data and portfolio information.

Installation:
    pip install pandas matplotlib tkinter

Author: Arthur Simon, MNr: 9227155
Date: 02.06.2024
license: free
version: 0.0.1 (master.major.minor)
"""

import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import tkinter as tk
from tkinter import messagebox
import datetime


def plot_historical_data(ticker: str, period: str, plot_frame: tk.Frame) -> None:
    """
    Plot historical data for a given ticker and period.

    Args:
        ticker (str): The stock or cryptocurrency ticker.
        period (str): The time period for the historical data.
        plot_frame (tk.Frame): The Tkinter frame to embed the plot.

    Raises:
        FileNotFoundError: If the data file for the ticker is not found.

    Returns:
        None

    Test Cases:
        1. Test with valid ticker and period, plot should be displayed without error.
        2. Test with invalid ticker, should raise FileNotFoundError and display an error message.
    """
    for widget in plot_frame.winfo_children():
        widget.destroy()

    try:
        data = pd.read_csv(f"data/{ticker}.csv", index_col="Date", parse_dates=True)
        fig, ax = plt.subplots(figsize=(10, 5))
        data["Close"].plot(ax=ax, title=f"{ticker} Closing Prices")
        ax.set_xlabel("Date")
        ax.set_ylabel("Price")
        ax.grid(True)

        canvas = FigureCanvasTkAgg(fig, master=plot_frame)
        canvas.draw()
        canvas.get_tk_widget().pack()

        plt.close(fig)
    except FileNotFoundError:
        messagebox.showerror("Error", "Historical data file not found. Please fetch the data first.")


def plot_portfolio(portfolio: dict, portfolio_plot_frame: tk.Frame, portfolio_value_history: list) -> None:
    """
    Plot the portfolio value over time.

    Args:
        portfolio (dict): The current portfolio holdings.
        portfolio_plot_frame (tk.Frame): The Tkinter frame to embed the plot.
        portfolio_value_history (list): The history of portfolio values over time.

    Returns:
        None

    Test Cases:
        1. Test with non-empty portfolio, plot should display correctly.
        2. Test with empty portfolio, plot should display an empty graph with correct titles.
    """
    for widget in portfolio_plot_frame.winfo_children():
        widget.destroy()

    tickers = list(portfolio['portfolio'].keys())
    fig, ax = plt.subplots(figsize=(10, 5))

    if not tickers:
        ax.plot([datetime.datetime.now()], [0], label="Invested Value")
        ax.set_title("Total Invested Value Over Time")
        ax.set_xlabel("Date")
        ax.set_ylabel("Value")
        ax.legend()
        ax.grid(True)
    else:
        for ticker in tickers:
            quantity = portfolio['portfolio'][ticker]
            data = pd.read_csv(f"data/{ticker}.csv", index_col="Date", parse_dates=True)
            current_price = data['Close'].iloc[-1]
            total_invested_value = current_price * quantity

        if portfolio_value_history:
            times, values = zip(*portfolio_value_history)
            ax.plot(times, values, label="Portfolio Value")
            ax.set_ylim(min(values) * 0.95, max(values) * 1.05)
        ax.set_title("Portfolio Value Over Time")
        ax.set_xlabel("Date")
        ax.set_ylabel("Value")
        ax.yaxis.set_major_formatter('${x:,.2f}')
        ax.grid(True)

    canvas = FigureCanvasTkAgg(fig, master=portfolio_plot_frame)
    canvas.draw()
    canvas.get_tk_widget().pack()

    plt.close(fig)
