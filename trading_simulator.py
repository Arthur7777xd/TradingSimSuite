"""
Trading Simulator Application
------------------------------
This module provides a trading simulator application with a graphical user interface using Tkinter.

Installation:
    pip install tkinter requests pandas matplotlib

Author: Arthur Simon, MNr: 9227155
Date: 02.06.2024
license: free
version: 0.0.1 (master.major.minor)
"""

import tkinter as tk
from tkinter import messagebox, ttk
import requests
import pandas as pd
from datetime import datetime
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from trading_utils import plot_historical_data, plot_portfolio
import json


class TradingSimulator(tk.Tk):
    """
    A GUI-based trading simulator application.
    """

    def __init__(self):
        """
        Initialize the trading simulator.

        Returns:
            None
        """
        super().__init__()
        self.title("Trading Simulator")
        self.geometry("800x600")
        self.configure(bg="lightgrey")

        self.remaining_capital = self.load_start_capital()
        self.portfolio_value = 0
        self.portfolio_value_history = []

        self.canvas = tk.Canvas(self, bg="lightgrey")
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        self.scrollbar.pack(side=tk.RIGHT, fill="y")

        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        self.canvas.bind('<Configure>', lambda e: self.canvas.configure(scrollregion=self.canvas.bbox('all')))
        self.canvas.bind_all("<MouseWheel>", self._on_mouse_wheel)

        self.frame = tk.Frame(self.canvas, bg="lightgrey")
        self.canvas.create_window((0, 0), window=self.frame, anchor="nw")

        self.create_widgets()
        self.load_initial_portfolio()
        self.previous_portfolio_value = 0
        self.update_portfolio_value()

    def _on_mouse_wheel(self, event) -> None:
        """
        Handle mouse wheel scrolling.

        Args:
            event: The event object.

        Returns:
            None

        Test Cases:
            1. Scroll with mouse wheel, canvas should scroll.
            2. Scroll with touchpad, canvas should scroll.
        """
        self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    def create_widgets(self) -> None:
        """
        Create and place widgets in the GUI.

        Returns:
            None

        Test Cases:
            1. Ensure all widgets are created and placed correctly.
            2. Check if widgets respond to user interactions correctly.
        """
        self.label = tk.Label(
            self.frame,
            text="Enter stock symbol (f.e. AAPL) or cryptocurrency symbol (BTC-USD):",
            bg="lightgrey",
            font=("Arial", 12)
        )
        self.label.pack(pady=10)

        self.query_entry = tk.Entry(self.frame, font=("Arial", 12))
        self.query_entry.pack(pady=10)
        self.query_entry.bind("<Return>", lambda event: self.get_historical_data())
        self.query_entry.bind("<KeyRelease>", self.uppercase_entry)

        self.search_frame = tk.Frame(self.frame, bg="lightgrey")
        self.search_frame.pack(pady=10)

        self.search_button = tk.Button(
            self.search_frame,
            text="Search Symbol",
            command=self.search_symbol,
            font=("Arial", 12),
            bg="white"
        )
        self.search_button.pack(side=tk.LEFT, padx=5)

        self.time_period_label = tk.Label(
            self.search_frame,
            text="Select Time Period:",
            bg="lightgrey",
            font=("Arial", 12)
        )
        self.time_period_label.pack(side=tk.LEFT, padx=5)

        self.valid_periods = ["1d", "5d", "1mo", "3mo", "6mo", "1y", "2y", "5y", "10y", "ytd", "max"]
        self.time_period_var = tk.StringVar(value="1y")
        self.time_period_menu = tk.OptionMenu(self.search_frame, self.time_period_var, *self.valid_periods, command=self.on_period_change)
        self.time_period_menu.config(font=("Arial", 12))
        self.time_period_menu.pack(side=tk.LEFT, padx=5)

        self.plot_frame = tk.Frame(self.frame, bg="lightgrey")
        self.plot_frame.pack(pady=20)

        self.quantity_label = tk.Label(self.frame, text="Enter Quantity:", bg="lightgrey", font=("Arial", 12))
        self.quantity_label.pack(pady=10)

        self.quantity_entry = tk.Entry(self.frame, font=("Arial", 12))
        self.quantity_entry.pack(pady=10)

        self.transaction_frame = tk.Frame(self.frame, bg="lightgrey")
        self.transaction_frame.pack(pady=10)

        self.buy_button = tk.Button(
            self.transaction_frame,
            text="Buy",
            command=self.buy_stock,
            font=("Arial", 12),
            bg="white"
        )
        self.buy_button.pack(side=tk.LEFT, padx=5)

        self.sell_button = tk.Button(
            self.transaction_frame,
            text="Sell",
            command=self.sell_stock,
            font=("Arial", 12),
            bg="white"
        )
        self.sell_button.pack(side=tk.LEFT, padx=5)

        self.portfolio_plot_frame = tk.Frame(self.frame, bg="lightgrey")
        self.portfolio_plot_frame.pack(pady=20)

        self.capital_label = tk.Label(
            self.frame,
            text=f"Remaining Capital: ${self.remaining_capital:.2f}",
            bg="lightgrey",
            font=("Arial", 12)
        )
        self.capital_label.pack(pady=10)

        self.portfolio_value_frame = tk.Frame(self.frame, bg="lightgrey")
        self.portfolio_value_frame.pack(pady=10)

        self.portfolio_value_label = tk.Label(
            self.portfolio_value_frame,
            text=f"Portfolio Value: $0.00",
            bg="lightgrey",
            font=("Arial", 12)
        )
        self.portfolio_value_label.pack(side=tk.LEFT, padx=5)

        self.portfolio_change_label = tk.Label(
            self.portfolio_value_frame,
            text="",
            bg="lightgrey",
            font=("Arial", 12)
        )
        self.portfolio_change_label.pack(side=tk.LEFT, padx=5)

        self.portfolio_list_label = tk.Label(
            self.frame,
            text="Portfolio Holdings:",
            bg="lightgrey",
            font=("Arial", 12)
        )
        self.portfolio_list_label.pack(pady=10)

        self.portfolio_listbox = tk.Listbox(self.frame, font=("Arial", 12), width=50, height=10)
        self.portfolio_listbox.pack(pady=10)

    def load_start_capital(self) -> float:
        """
        Load the starting capital from a configuration file.

        Returns:
            float: The starting capital.

        Test Cases:
            1. Ensure the start capital is loaded correctly from the JSON file.
            2. Handle cases where the file or the 'start_capital' key does not exist.
        """
        with open('portfolio.json', 'r') as f:
            config = json.load(f)
        return config['start_capital']

    def load_initial_portfolio(self) -> None:
        """
        Load the initial portfolio data from the server.

        Raises:
            RuntimeError: If the request to the server fails.

        Returns:
            None

        Test Cases:
            1. Ensure the initial portfolio is loaded and displayed correctly.
            2. Handle server response errors correctly.
        """
        response = requests.get("http://127.0.0.1:8000/portfolio")
        if response.status_code == 200:
            portfolio = response.json()
            plot_portfolio(portfolio, self.portfolio_plot_frame, self.portfolio_value_history)
            self.update_portfolio_list(portfolio['portfolio'])
        else:
            raise RuntimeError(response.json()['detail'])

    def search_symbol(self) -> None:
        """
        Search for a stock or cryptocurrency symbol.

        Raises:
            RuntimeError: If the request to the server fails.

        Returns:
            None

        Test Cases:
            1. Ensure the search result is displayed correctly for a valid symbol.
            2. Handle server response errors correctly.
        """
        query = self.query_entry.get()
        response = requests.get(f"http://127.0.0.1:8000/search/{query.upper()}")
        if response.status_code == 200:
            result = response.json()
            symbol = result['symbol']
            name = result['name']
            messagebox.showinfo("Search Result", f"Symbol: {symbol}\nName: {name}")
            self.query_entry.delete(0, tk.END)
            self.query_entry.insert(0, symbol)
        else:
            raise RuntimeError(response.json()['detail'])

    def get_historical_data(self) -> None:
        """
        Fetch historical data for the specified ticker.

        Raises:
            RuntimeError: If the request to the server fails.

        Returns:
            None

        Test Cases:
            1. Ensure historical data is fetched and plotted correctly.
            2. Handle server response errors correctly.
        """
        ticker = self.query_entry.get().upper()
        period = self.time_period_var.get()
        response = requests.get(f"http://127.0.0.1:8000/historical-data/{ticker}?period={period}")
        if response.status_code == 200:
            messagebox.showinfo("Success", response.json()['message'])
            plot_historical_data(ticker, period, self.plot_frame)
        else:
            raise RuntimeError(response.json()['detail'])

    def on_period_change(self, event) -> None:
        """
        Handle the change in selected time period.

        Args:
            event: The event object.

        Returns:
            None

        Test Cases:
            1. Ensure the historical data is updated when the period changes.
            2. Verify no errors occur when changing the period.
        """
        self.get_historical_data()

    def buy_stock(self) -> None:
        """
        Buy the specified quantity of stock.

        Raises:
            RuntimeError: If the request to the server fails.
            ValueError: If the quantity is not valid.

        Returns:
            None

        Test Cases:
            1. Ensure stock is bought and portfolio is updated correctly.
            2. Handle server response errors and invalid input correctly.
        """
        ticker = self.query_entry.get().upper()
        quantity = self.quantity_entry.get()
        if not quantity.isdigit():
            raise ValueError("Please enter a valid quantity.")
    
        quantity = int(quantity)
        response = requests.post(f"http://127.0.0.1:8000/buy", params={"ticker": ticker, "quantity": quantity})
        if response.status_code == 200:
            result = response.json()
            messagebox.showinfo("Success", result['message'])
            self.update_portfolio(result['total_value'], result['remaining_capital'])
            self.update_portfolio_list(result['portfolio'])
        else:
            if response.json()['detail'] == "Please fetch the historical data for this ticker before making a purchase.":
                self.get_historical_data()
            raise RuntimeError(response.json()['detail'])

    def sell_stock(self) -> None:
        """
        Sell the specified quantity of stock.

        Raises:
            RuntimeError: If the request to the server fails.
            ValueError: If the quantity is not valid.

        Returns:
            None

        Test Cases:
            1. Ensure stock is sold and portfolio is updated correctly.
            2. Handle server response errors and invalid input correctly.
        """
        ticker = self.query_entry.get().upper()
        quantity = self.quantity_entry.get()
        if not quantity.isdigit():
            raise ValueError("Please enter a valid quantity.")

        quantity = int(quantity)
        response = requests.post(f"http://127.0.0.1:8000/sell", params={"ticker": ticker, "quantity": quantity})
        if response.status_code == 200:
            result = response.json()
            messagebox.showinfo("Success", result['message'])
            self.update_portfolio(result['total_value'], result['remaining_capital'])
            self.update_portfolio_list(result['portfolio'])
        else:
            raise RuntimeError(response.json()['detail'])

    def update_portfolio(self, total_value: float, remaining_capital: float) -> None:
        """
        Update the portfolio value and remaining capital.

        Args:
            total_value (float): The total value of the portfolio.
            remaining_capital (float): The remaining capital after the transaction.

        Returns:
            None

        Test Cases:
            1. Ensure portfolio value and remaining capital are updated correctly.
            2. Verify the portfolio value history is recorded correctly.
        """
        self.portfolio_value_label.config(text=f"Portfolio Value: ${total_value:.2f}")
        self.capital_label.config(text=f"Remaining Capital: ${remaining_capital:.2f}")
        self.portfolio_value_history.append((datetime.now(), total_value))
        self.show_portfolio()

    def show_portfolio(self) -> None:
        """
        Display the current portfolio.

        Raises:
            RuntimeError: If the request to the server fails.

        Returns:
            None

        Test Cases:
            1. Ensure the portfolio is displayed correctly.
            2. Handle server response errors correctly.
        """
        response = requests.get("http://127.0.0.1:8000/portfolio")
        if response.status_code == 200:
            portfolio = response.json()
            plot_portfolio(portfolio, self.portfolio_plot_frame, self.portfolio_value_history)
            self.update_portfolio_list(portfolio['portfolio'])
        else:
            raise RuntimeError(response.json()['detail'])

    def update_portfolio_value(self) -> None:
        """
        Update the value of the portfolio.

        Raises:
            RuntimeError: If the request to the server fails.

        Returns:
            None

        Test Cases:
            1. Ensure the portfolio value is updated correctly at regular intervals.
            2. Handle server response errors correctly.
        """
        response = requests.get("http://127.0.0.1:8000/portfolio-value")
        if response.status_code == 200:
            total_invested_value = response.json()['total_value']
            self.portfolio_value_label.config(text=f"Portfolio Value: ${total_invested_value:.2f}")

            change = total_invested_value - self.previous_portfolio_value
            if change > 0:
                self.portfolio_change_label.config(text=f"↑ ${change:.2f}", fg="green")
            elif change < 0:
                self.portfolio_change_label.config(text=f"↓ ${-change:.2f}", fg="red")
            else:
                self.portfolio_change_label.config(text="")

            self.previous_portfolio_value = total_invested_value

            portfolio_response = requests.get("http://127.0.0.1:8000/portfolio")
            if portfolio_response.status_code == 200:
                portfolio = portfolio_response.json()
                self.portfolio_value_history.append((datetime.now(), total_invested_value))
                plot_portfolio(portfolio, self.portfolio_plot_frame, self.portfolio_value_history)

        self.after(60000, self.update_portfolio_value)

    def update_portfolio_list(self, portfolio: dict) -> None:
        """
        Update the portfolio list displayed in the GUI.

        Args:
            portfolio (dict): The current portfolio holdings.

        Returns:
            None

        Test Cases:
            1. Ensure the portfolio list is updated correctly.
            2. Verify the displayed quantities are accurate.
        """
        self.portfolio_listbox.delete(0, tk.END)
        for ticker, quantity in portfolio.items():
            self.portfolio_listbox.insert(tk.END, f"{ticker}: {quantity} shares")

    def uppercase_entry(self, event) -> None:
        """
        Convert the entry text to uppercase.

        Args:
            event: The event object.

        Returns:
            None

        Test Cases:
            1. Ensure the entry text is converted to uppercase correctly.
            2. Verify no errors occur during conversion.
        """
        content = self.query_entry.get()
        self.query_entry.delete(0, tk.END)
        self.query_entry.insert(0, content.upper())


if __name__ == "__main__":
    app = TradingSimulator()
    app.mainloop()
