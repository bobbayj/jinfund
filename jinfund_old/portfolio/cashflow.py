# Standard imports
import pandas as pd

# Local Imports
from portfolio.transactions import Trades


class Cashflow(object):
    def __init__(self):
        trades = Trades()
        self.trades = trades.tx_df

    def tx_cash_balance(self):
        




