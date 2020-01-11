# System imports
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# Third-party imports

# Local imports
from trades.commsec import Trades
import datehandler
# from yahoolookup import Stock

class Portfolio:

    def __init__(self):
    # Create portfolio from trades
        trades = Trades()
        self.df_txs = trades.all()
        self.daily_holdings = self.build_from_txs()

    def build_from_txs(self):
        df = self.df_txs

        inception_date = df.index[-1]
        date_today = datetime.today().date()
        portfolio_dates = datehandler.date_list(inception_date, date_today)
        portfolio_holdings = {key: None for key in portfolio_dates}

        trade_dates = df.index.to_list()
        trade_tickers = df.Ticker.to_list()
        trade_types = df.TradeType.to_list()
        trade_volumes = df.Volume.to_list()
        trade_prices = df.EffectivePrice.to_list()

        holdings = {
            'cash':0,
            }

        trade_date = trade_dates.pop()
        for portfolio_date in sorted(portfolio_dates, reverse=False):
            while trade_date == portfolio_date:
                trade_ticker = trade_tickers.pop()
                trade_type = trade_types.pop()
                trade_vol = trade_volumes.pop()
                trade_price = trade_prices.pop()

                if trade_ticker in holdings:
                    if trade_type == 'B':
                        new_vol = holdings[trade_ticker]['vol'] + trade_vol
                        new_vwap = (holdings[trade_ticker]['vol']*holdings[trade_ticker]['vwap'] + trade_vol*trade_price) / new_vol
                        holdings[trade_ticker] = {
                            'vol': new_vol,
                            'vwap': np.round(new_vwap, decimals=3),
                            }
                        holdings['cash'] -= np.round(trade_vol*trade_price, decimals=3)
                    else:
                        holdings[trade_ticker]['vol'] -= trade_vol
                        holdings['cash'] += np.round(trade_vol*trade_price, decimals=3)
                else:
                    holdings[trade_ticker] = {
                        'vol': trade_vol,
                        'vwap': np.round(trade_price, decimals=3),
                    }
                    holdings['cash'] -= np.round(trade_vol*trade_price, decimals=3)
                
                if len(trade_dates) > 0:
                    trade_date = trade_dates.pop()
                else:
                    break
            
            portfolio_holdings[portfolio_date] = holdings
        
        return portfolio_holdings

    def view(self,date):
        # Convert date to datetime.date

        dates = list(self.daily_holdings.keys())
        
        self.daily_holdings[date]
