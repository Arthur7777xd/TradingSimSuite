# frontend/gui.py

import tkinter as tk
from tkinter import messagebox, ttk
import requests
import json
import matplotlib.pyplot as plt
import pandas as pd
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from datetime import datetime, timedelta

class TradingSimulator(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Trading Simulator")
        self.geometry("800x600")
        self.configure(bg="lightgrey")

        self.remaining_capital = self.load_start_capital()

        # Create a canvas to add scrollbars
        self.canvas = tk.Canvas(self, bg="lightgrey")
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        self.scrollbar.pack(side=tk.RIGHT, fill="y")

        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        self.canvas.bind('<Configure>', lambda e: self.canvas.configure(scrollregion=self.canvas.bbox('all')))

        self.frame = tk.Frame(self.canvas, bg="lightgrey")
        self.canvas.create_window((0, 0), window=self.frame, anchor="nw")

        self.create_widgets()
        self.plot_portfolio({"portfolio": {}, "remaining_capital": self.remaining_capital})  # Plot default portfolio with value 0

    def create_widgets(self):
        self.label = tk.Label(self.frame, text="Enter Company Name or Ticker Symbol:", bg="lightgrey", font=("Arial", 12))
        self.label.pack(pady=10)

        self.query_entry = tk.Entry(self.frame, font=("Arial", 12))
        self.query_entry.pack(pady=10)
        self.query_entry.bind("<Return>", lambda event: self.get_historical_data())

        self.search_button = tk.Button(self.frame, text="Search Symbol", command=self.search_symbol, font=("Arial", 12), bg="white")
        self.search_button.pack(pady=10)

        self.plot_frame = tk.Frame(self.frame, bg="lightgrey")
        self.plot_frame.pack(pady=20)

        self.quantity_label = tk.Label(self.frame, text="Enter Quantity:", bg="lightgrey", font=("Arial", 12))
        self.quantity_label.pack(pady=10)

        self.quantity_entry = tk.Entry(self.frame, font=("Arial", 12))
        self.quantity_entry.pack(pady=10)

        self.buy_button = tk.Button(self.frame, text="Buy", command=self.buy_stock, font=("Arial", 12), bg="white")
        self.buy_button.pack(pady=10)

        self.sell_button = tk.Button(self.frame, text="Sell", command=self.sell_stock, font=("Arial", 12), bg="white")
        self.sell_button.pack(pady=10)

        self.time_period_label = tk.Label(self.frame, text="Select Time Period:", bg="lightgrey", font=("Arial", 12))
        self.time_period_label.pack(pady=10)

        self.valid_periods = ["1d", "5d", "1mo", "3mo", "6mo", "1y", "2y", "5y", "10y", "ytd", "max"]
        self.time_period_var = tk.StringVar(value="1y")
        self.time_period_menu = tk.OptionMenu(self.frame, self.time_period_var, *self.valid_periods, command=self.on_period_change)
        self.time_period_menu.config(font=("Arial", 12))
        self.time_period_menu.pack(pady=10)

        self.portfolio_plot_frame = tk.Frame(self.frame, bg="lightgrey")
        self.portfolio_plot_frame.pack(pady=20)

        self.capital_label = tk.Label(self.frame, text=f"Remaining Capital: ${self.remaining_capital:.2f}", bg="lightgrey", font=("Arial", 12))
        self.capital_label.pack(pady=10)

    def load_start_capital(self):
        with open('config.json', 'r') as f:
            config = json.load(f)
        return config['start_capital']

    def search_symbol(self):
        query = self.query_entry.get()
        response = requests.get(f"http://127.0.0.1:8000/search/{query}")
        if response.status_code == 200:
            result = response.json()
            symbol = result['symbol']
            name = result['name']
            messagebox.showinfo("Search Result", f"Symbol: {symbol}\nName: {name}")
            self.query_entry.delete(0, tk.END)
            self.query_entry.insert(0, symbol)
        else:
            messagebox.showerror("Error", response.json()['detail'])

    def get_historical_data(self):
        ticker = self.query_entry.get()
        period = self.time_period_var.get()
        response = requests.get(f"http://127.0.0.1:8000/historical-data/{ticker}?period={period}")
        if response.status_code == 200:
            messagebox.showinfo("Success", response.json()['message'])
            self.plot_historical_data(ticker, period)
        else:
            messagebox.showerror("Error", response.json()['detail'])

    def on_period_change(self, event):
        self.get_historical_data()

    def plot_historical_data(self, ticker, period):
        for widget in self.plot_frame.winfo_children():
            widget.destroy()

        try:
            data = pd.read_csv(f"data/{ticker}.csv", index_col="Date", parse_dates=True)
            fig, ax = plt.subplots(figsize=(10, 5))
            data["Close"].plot(ax=ax, title=f"{ticker} Closing Prices")
            ax.set_xlabel("Date")
            ax.set_ylabel("Price")
            ax.grid(True)

            canvas = FigureCanvasTkAgg(fig, master=self.plot_frame)
            canvas.draw()
            canvas.get_tk_widget().pack()
        except FileNotFoundError:
            messagebox.showerror("Error", "Historical data file not found. Please fetch the data first.")

    def buy_stock(self):
        ticker = self.query_entry.get()
        quantity = self.quantity_entry.get()
        if not quantity.isdigit():
            messagebox.showerror("Error", "Please enter a valid quantity.")
            return

        quantity = int(quantity)
        response = requests.post(f"http://127.0.0.1:8000/buy", params={"ticker": ticker, "quantity": quantity})
        if response.status_code == 200:
            messagebox.showinfo("Success", response.json()['message'])
            self.show_portfolio()  # Update the portfolio after buying
        else:
            messagebox.showerror("Error", response.json()['detail'])

    def sell_stock(self):
        ticker = self.query_entry.get()
        quantity = self.quantity_entry.get()
        if not quantity.isdigit():
            messagebox.showerror("Error", "Please enter a valid quantity.")
            return

        quantity = int(quantity)
        response = requests.post(f"http://127.0.0.1:8000/sell", params={"ticker": ticker, "quantity": quantity})
        if response.status_code == 200:
            messagebox.showinfo("Success", response.json()['message'])
            self.show_portfolio()  # Update the portfolio after selling
        else:
            messagebox.showerror("Error", response.json()['detail'])

    def show_portfolio(self):
        response = requests.get(f"http://127.0.0.1:8000/portfolio")
        if response.status_code == 200:
            portfolio = response.json()
            self.remaining_capital = portfolio['remaining_capital']
            self.capital_label.config(text=f"Remaining Capital: ${self.remaining_capital:.2f}")
            self.plot_portfolio(portfolio)
        else:
            messagebox.showerror("Error", response.json()['detail'])

    def plot_portfolio(self, portfolio):
        for widget in self.portfolio_plot_frame.winfo_children():
            widget.destroy()

        total_invested_value = 0
        tickers = list(portfolio['portfolio'].keys())

        fig, ax = plt.subplots(figsize=(10, 5))

        if not tickers:  # No investments
            ax.plot([datetime.now()], [0], label="Invested Value")
            ax.set_title("Total Invested Value Over Time")
            ax.set_xlabel("Date")
            ax.set_ylabel("Value")
            ax.legend()
            ax.grid(True)
        else:
            for ticker in tickers:
                quantity = portfolio['portfolio'][ticker]
                data = pd.read_csv(f"data/{ticker}.csv", index_col="Date", parse_dates=True)
                current_price = data['Close'].iloc[-1]  # Use .iloc for position-based indexing
                total_invested_value += current_price * quantity

            ax.plot(data.index, [total_invested_value] * len(data.index), label="Invested Value")
            ax.set_title("Total Invested Value Over Time")
            ax.set_xlabel("Date")
            ax.set_ylabel("Value")
            ax.legend()
            ax.grid(True)

        canvas = FigureCanvasTkAgg(fig, master=self.portfolio_plot_frame)
        canvas.draw()
        canvas.get_tk_widget().pack()

if __name__ == "__main__":
    app = TradingSimulator()
    app.mainloop()
