# frontend/gui.py

import tkinter as tk
from tkinter import messagebox
import requests
import matplotlib.pyplot as plt
import pandas as pd
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

class TradingSimulator(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Trading Simulator")
        self.geometry("1400x1000")
        self.create_widgets()

    def create_widgets(self):
        self.label = tk.Label(self, text="Enter Company Name or Ticker Symbol:")
        self.label.pack(pady=10)

        self.query_entry = tk.Entry(self)
        self.query_entry.pack(pady=10)

        self.search_button = tk.Button(self, text="Search Symbol", command=self.search_symbol)
        self.search_button.pack(pady=10)

        self.get_data_button = tk.Button(self, text="Get Historical Data", command=self.get_historical_data)
        self.get_data_button.pack(pady=10)

        self.plot_frame = tk.Frame(self)
        self.plot_frame.pack(pady=20)

        self.quantity_label = tk.Label(self, text="Enter Quantity:")
        self.quantity_label.pack(pady=10)

        self.quantity_entry = tk.Entry(self)
        self.quantity_entry.pack(pady=10)

        self.buy_button = tk.Button(self, text="Buy", command=self.buy_stock)
        self.buy_button.pack(pady=10)

        self.sell_button = tk.Button(self, text="Sell", command=self.sell_stock)
        self.sell_button.pack(pady=10)

        self.portfolio_button = tk.Button(self, text="Show Portfolio", command=self.show_portfolio)
        self.portfolio_button.pack(pady=10)

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
        response = requests.get(f"http://127.0.0.1:8000/historical-data/{ticker}")
        if response.status_code == 200:
            messagebox.showinfo("Success", response.json()['message'])
            self.plot_historical_data(ticker)
        else:
            messagebox.showerror("Error", response.json()['detail'])

    def plot_historical_data(self, ticker):
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
        else:
            messagebox.showerror("Error", response.json()['detail'])

    def show_portfolio(self):
        response = requests.get(f"http://127.0.0.1:8000/portfolio")
        if response.status_code == 200:
            portfolio = response.json()
            portfolio_str = f"Portfolio:\n\n"
            for ticker, quantity in portfolio['portfolio'].items():
                portfolio_str += f"{ticker}: {quantity} shares\n"
            portfolio_str += f"\nRemaining Capital: {portfolio['remaining_capital']}"
            messagebox.showinfo("Portfolio", portfolio_str)
        else:
            messagebox.showerror("Error", response.json()['detail'])

if __name__ == "__main__":
    app = TradingSimulator()
    app.mainloop()
