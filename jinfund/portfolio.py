# System imports
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import copy

# Third-party imports

# Local imports
from trades.commsec import Trades
import datehandler
import yahoolookup

class Portfolio:

    def __init__(self):
        # Create portfolio from trades
        trades = Trades()
        self.df_txs = trades.all()
        self.portfolio_dates = datehandler.date_list(self.df_txs.index[-1], datetime.today().date())
        self.daily_holdings = self.build_portfolio()

    def build_portfolio(self):
        portfolio_df = self.build_df_from_txs()
        portfolio_df = self.add_divs_splits(portfolio_df)
        # portfolio_df = self.add_scrip_remove_div(portfolio_df)
        return portfolio_df

    def build_df_from_txs(self):
        '''Builds daily portfolio holdings from broker transactions data
        
        Returns:
            DataFrame -- index = datetime.date | columns = tickers | values = {'vol', 'vwap'}
        '''
        trade_dates = self.df_txs.index.to_list()
        trade_tickers = self.df_txs.Ticker.to_list()
        trade_types = self.df_txs.TradeType.to_list()
        trade_volumes = self.df_txs.Volume.to_list()
        trade_prices = self.df_txs.EffectivePrice.to_list()
        
        portfolio_holdings = {key: None for key in self.portfolio_dates}

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
            portfolio_holdings[portfolio_date] = copy.deepcopy(holdings)  # To preserve the mutability of each daily holding

        portfolio_df = pd.DataFrame.from_dict(
            portfolio_holdings,
            orient='index'
            )
        portfolio_df.index.names = ['Date']

        return portfolio_df

    def add_divs_splits(self, portfolio_df):
        '''Reflects cash dividends and stocksplits in the portfolio dataframe.
        This uses public data; scrip dividends are not reflected, which are personal in nature
        
        Arguments:
            portfolio_df {dataframe} -- Portfolio dataframe created from transactions
        
        Returns:
            dataframe -- Portfolio dataframe with cash dividend and splits as new keys. Vol and price also changed for splits
        '''        
        tickers = portfolio_df.columns.to_list()
        for counter,ticker in enumerate(tickers):
            print(f'\rFetching {ticker} corporate actions...'
                f'Progress: {counter}/{len(tickers)-1}',
                end="", flush=True
            )

            if ticker != 'cash':
                market = self.df_txs[self.df_txs['Ticker']==ticker].Market.iloc[0]
                stock = yahoolookup.Stock(ticker, market)
                try:  # Catch if the stock has been delisted/is invalid
                    actions = stock.actions()
                    if len(actions) == 0:
                        continue
                except:  # Issue fetching stock data...yfinance will show error and we skip
                    continue
                
                actions.index = actions.index.date
                mask_actions = (actions.index >= portfolio_df[ticker].last_valid_index())
                actions = actions.loc[mask_actions]
                
                for action_date, row in actions.iterrows():
                    div = row['Dividends']
                    split = row['Stock Splits']
                    if div > 0:
                        portfolio_df.at[action_date,ticker]['div'] = div
                    if split > 0:
                        portfolio_df.at[action_date,ticker]['split'] = split

                        # Update all vols and VWAPs after this to reflect split
                        mask_split = (portfolio_df.index >= action_date)
                        dates_to_update_with_split = portfolio_df.loc[mask_split, ticker]
                        for holding in dates_to_update_with_split.array:
                            holding['vol'] = holding['vol'] * split
                            holding['vwap'] = holding['vwap'] / split

        return portfolio_df

    def add_scrip_remove_div(self, portfolio_df):
        # Read csv of scrip receives - this is manually maintained
            # Columns: date, ticker, vol
        pass

    def view(self, start_date=datetime.today().date(), end_date=None):
        '''Fetches porfolio holdings of the given date. Will attempt to convert the lookup date to datetime.date format
        
        Keyword Arguments:
            lookup_date {str, datetime.date} -- Date to lookup portfolio (default: {datetime.today().date()})
        
        Returns:
            dict -- All holdings as of lookup_date
        '''
        start_date = datehandler.to_iso(start_date)

        if end_date:
            end_date = datehandler.to_iso(end_date)
            mask = (self.daily_holdings.index > start_date) & (self.daily_holdings.index <= end_date)
        else:
            if start_date not in self.portfolio_dates:
                start_date = self.portfolio_dates[0]
            mask = (self.daily_holdings.index == start_date)
    
        return self.daily_holdings.loc[mask]
