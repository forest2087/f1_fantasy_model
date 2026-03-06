import pandas as pd
from IPython.display import display
import json

# https://docs.google.com/spreadsheets/d/1b5486fzknvQgXJxPuS7U88HwMYLrz-EfdfTO3-w5qx0/pub?output=csv

url = "https://docs.google.com/spreadsheets/d/1b5486fzknvQgXJxPuS7U88HwMYLrz-EfdfTO3-w5qx0/pub?output=csv"
_prices = pd.read_csv(url)

# driver_prices.to_csv('_prices.csv', index=False)

_prices.set_index('Name', inplace=True)


display(_prices['CurrentPrice'].to_dict())

driver_prices = _prices.iloc[:20]['CurrentPrice'].to_dict()

constructor_prices = _prices.iloc[20:30]['CurrentPrice'].to_dict()

display(driver_prices)
display(constructor_prices)
