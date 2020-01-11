# System imports
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# Third-party imports

# Local imports
from trades.commsec import Trades
import datehandler
from yahoolookup import Stock

class Portfolio:

    def __init__(self):
        # Create portfolio from trades
        trades = Trades()
        self.df_txs = trades.all()
        self.portfolio_dates = None

        self.daily_holdings = self.build_from_txs()

    def build_from_txs(self):
        '''Builds daily portfolio holdings from transactions data
        
        Returns:
            dict -- keys = dates in datetime.date | values = {tickers: 'vol', 'vwap'}
        '''
        df = self.df_txs

        inception_date = df.index[-1]
        today = datetime.today().date()
        self.portfolio_dates = datehandler.date_list(inception_date, today)
        portfolio_holdings = {key: None for key in self.portfolio_dates}

        trade_dates = df.index.to_list()
        trade_tickers = df.Ticker.to_list()
        trade_types = df.TradeType.to_list()
        trade_volumes = df.Volume.to_list()
        trade_prices = df.EffectivePrice.to_list()

        holdings = {
            'cash':0,
            }

        trade_date = trade_dates.pop()
        for portfolio_date in sorted(self.portfolio_dates, reverse=False):
            while trade_date == portfolio_date:
                trade_ticker = trade_tickers.pop()
                trade_type = trade_types.pop()
                trade_vol = trade_volumes.pop()
                trade_price = trade_prices.pop()

                if trade_ticker in holdings:
                    if trade_type == 'B':  # Trade is a buy
                        new_vol = holdings[trade_ticker]['vol'] + trade_vol
                        new_vwap = (
                            (holdings[trade_ticker]['vol']*holdings[trade_ticker]['vwap']
                            + trade_vol*trade_price) / new_vol
                        )
                        holdings[trade_ticker] = {
                            'vol': new_vol,
                            'vwap': np.round(new_vwap, decimals=3),
                            }
                        holdings['cash'] -= np.round(trade_vol*trade_price, decimals=3)
                    else:  # Trade is a sale
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
            portfolio_holdings[portfolio_date] = holdings.copy()
        return portfolio_holdings

    def add_divs(self, ticker, show_divs=False):
        market = self.df_txs[self.df_txs['Ticker']==ticker].Market.iloc[0]
        stock = Stock(ticker, market)
        divs = stock.dividends()

        divs.index = divs.index.date
        
        if len(divs) < 1:
            return
        
        for date, div in divs.items():
            print(type(date))
            print(self.daily_holdings.at[date,ticker], date, div)
            # self.daily_holdings.at[date,ticker]['div'] = div
            self.daily_holdings.loc[date].at[ticker]['div'] = div
        if show_divs:
            print(divs)
        return divs

    def add_stocksplits(self, ticker):
        pass

    def view(self, start_date=datetime.today().date(), end_date=None):
        '''Fetches porfolio holdings of the given date. Will attempt to convert the lookup date to datetime.date format
        
        Keyword Arguments:
            lookup_date {str, datetime.date} -- Date to lookup portfolio (default: {datetime.today().date()})
        
        Returns:
            dict -- All holdings as of lookup_date
        '''
        start_date = datehandler.to_iso(start_date)
        view_df = pd.DataFrame()

        if end_date:
            end_date = datehandler.to_iso(end_date)
            dates = datehandler.date_list(start_date, end_date)
            for date in dates:
                if date in self.portfolio_dates:
                    df = pd.DataFrame.from_dict(
                        {date: self.daily_holdings[date]},
                        orient='index'
                        )
                    view_df = view_df.append(df)
        else:
            if start_date not in self.portfolio_dates:
                start_date = self.portfolio_dates[0]
            
            view_df = pd.DataFrame.from_dict(
                {start_date: self.daily_holdings[start_date]},
                orient='index'
                )

        return view_df
