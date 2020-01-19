# System imports
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import copy
from pathlib import Path

# Third-party imports

# Local imports
from portfolio.commsec import Trades
import datehandler
import yahoolookup


class Portfolio:

    def __init__(self):
        # Create portfolio from trades
        self.trades = Trades()
        self.df_txs = self.trades.all
        self.portfolio_dates = datehandler.date_list(self.df_txs.index[-1], datetime.today().date())
        self.daily_holdings = self.build_portfolio()

    def build_portfolio(self):
        save_dir = Path(__file__).parents[1] / 'data'
        today = datetime.today().date()
        check_date = datehandler.date_list(today-timedelta(5),today)[0]
        portfolio_csv_name = f'portfolio_{check_date}.csv'
        portfolio_csv_path = save_dir / portfolio_csv_name

        if portfolio_csv_path.is_file():
            portfolio_df = pd.read_csv(portfolio_csv_path,
                                       parse_dates=True, dayfirst=True,
                                       index_col=0, header=[0,1],
                                       )
            portfolio_df.index = pd.to_datetime(portfolio_df.index)
            print(f'Latest portfolio loaded: {check_date}')
        else:
            portfolio_df = self._build_df_from_txs()
            portfolio_df = self._add_divs_splits(portfolio_df)
            # portfolio_df = self.add_scrip_remove_div(portfolio_df)
            portfolio_df = self._fill_daily_prices(portfolio_df)
            portfolio_df = self._calculate_value(portfolio_df)

            # Save as csv
            save_name = f'portfolio_{portfolio_df.index[-1].date()}.csv'
            save_path = save_dir / save_name
            portfolio_df.to_csv(save_path)
            print(f'\nLatest portfolio created: {check_date}')

        portfolio_df = self._sort_df(portfolio_df)
        return portfolio_df

    def returns(self, start_date, end_date=None):
        # Numerator: End value - (initial value + cashflow)
        # Denominator: Initial value + cashflow
        # Cashflow comes from the cash vol


        if end_date not in self.portfolio_dates:
                end_date = self.portfolio_dates[0]


        return

    def view(self, start_date=datetime.today(), end_date=None):
        '''Fetches porfolio holdings of the given date. Will attempt to convert the lookup date to datetime.date format

        Keyword Arguments:
            lookup_date {str, datetime.date} -- Date to lookup portfolio (default: {datetime.today()})

        Returns:
            dict -- All holdings as of lookup_date
        '''
        start_date = datehandler.to_iso(start_date)

        if end_date:
            end_date = datehandler.to_iso(end_date)
            mask = (self.daily_holdings.index >= start_date) & (self.daily_holdings.index <= end_date)
        else:
            if start_date not in self.portfolio_dates:
                start_date = self.portfolio_dates[0]
            mask = start_date
        return self.daily_holdings.loc[mask]

    def _calculate_value(self, df):
        # Calculate value of each ticker per day
        for ticker in df.columns.levels[0]:
            df.loc[:,(ticker,'book_value')] = df[ticker]['vol'] * df[ticker]['vwap']
            df.loc[:,(ticker,'market_value')] = df[ticker]['vol'] * df[ticker]['close_price']

        return df

    def _sort_df(self,df):
        df = df.reindex(sorted(df.columns),axis=1)
        return df

    def _fill_daily_prices(self, df):
        for counter, ticker in enumerate(df.columns.levels[0]):
            if ticker == 'cash':
                continue

            print(f'\rFetching {ticker} corporate actions...'
                f'Progress: {counter+1}/{len(df.columns.levels[0])-1}',
                end="", flush=True
                )

            market = self.df_txs[self.df_txs['Ticker'] == ticker].Market.iloc[0]
            stock = yahoolookup.Stock(ticker, market)
            start_date = df[ticker].first_valid_index().date()
            end_date = df[ticker].last_valid_index().date()
            try:  # Catch if the stock has been delisted/is invalid
                close_price = stock.history(start=start_date, end=end_date)['Close']
            except Exception as e:  # Issue fetching stock data...yfinance will show error and we skip
                print(f'{e}: Skipping...')
                continue
            
            df[(ticker, 'close_price')] = close_price

        return df

    def _build_df_from_txs(self):
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
            'cash': {'vol': 0, 'vwap': 1},
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
                        holdings['cash']['vol'] -= np.round(trade_vol*trade_price, decimals=3)
                    else:  # Trade is a sale
                        holdings[trade_ticker]['vol'] -= trade_vol
                        holdings['cash']['vol'] += np.round(trade_vol*trade_price, decimals=3)
                else:
                    holdings[trade_ticker] = {
                        'vol': trade_vol,
                        'vwap': np.round(trade_price, decimals=3),
                    }
                    holdings['cash']['vol'] -= np.round(trade_vol*trade_price, decimals=3)
                
                if len(trade_dates) > 0:
                    trade_date = trade_dates.pop()
                else:
                    break
            portfolio_holdings[portfolio_date] = copy.deepcopy(holdings)  # To preserve the mutability of each daily holding

        # Multilevel dataframe makes it easier to edit
        reform = {
            (level1_key, level2_key, level3_key): values
            for level1_key, level2_dict in portfolio_holdings.items()
            for level2_key, level3_dict in level2_dict.items()
            for level3_key, values in level3_dict.items()
            }
        portfolio_df = pd.Series(reform).unstack(level=[1,2])
        portfolio_df.index.names = ['Date']
        portfolio_df.columns.names = ['Tickers','Props']

        return portfolio_df

    def _add_divs_splits(self, portfolio_df):
        '''Reflects cash dividends and stocksplits in the portfolio dataframe.
        This uses public data; scrip dividends are not reflected, which are personal in nature
        
        Arguments:
            portfolio_df {dataframe} -- Portfolio dataframe created from transactions
        
        Returns:
            dataframe -- Portfolio dataframe with cash dividend and splits as new keys. Vol and price also changed for splits
        '''        
        for counter,ticker in enumerate(portfolio_df.columns.levels[0]):
            if ticker == 'cash':
                continue
            
            print(f'\rFetching {ticker} corporate actions...'
                f'Progress: {counter+1}/{len(portfolio_df.columns.levels[0])-1}',
                end="", flush=True
                )

            market = self.df_txs[self.df_txs['Ticker'] == ticker].Market.iloc[0]
            stock = yahoolookup.Stock(ticker, market)
            try:  # Catch if the stock has been delisted/is invalid
                actions = stock.actions()
                if len(actions) == 0:
                    continue
            except Exception as e:  # Issue fetching stock data...yfinance will show error and we skip
                print(f'{e}: Skipping...')
                continue
            
            actions.index = pd.to_datetime(actions.index)
            mask_actions = (actions.index >= portfolio_df[ticker].first_valid_index())
            actions = actions.loc[mask_actions]

            for action_date, row in actions.iterrows():
                div = row['Dividends']
                split = row['Stock Splits']
                if div > 0:
                    portfolio_df.at[action_date, (ticker,'div')] = div
                if split > 0:
                    portfolio_df.at[action_date, (ticker,'split')] = split

                    # Update all vols and VWAPs after this to reflect split
                    mask_split = (portfolio_df.index >= action_date)
                    slice_to_update = portfolio_df.loc[mask_split]
                    for i, row in slice_to_update[ticker].iterrows():
                        portfolio_df.at[i, (ticker,'vol')] = portfolio_df.at[i, (ticker,'vol')] * split
                        portfolio_df.at[i, (ticker,'vwap')] = portfolio_df.at[i, (ticker,'vwap')] / split

        return portfolio_df

    def _add_scrip_remove_div(self, portfolio_df):
        # Read csv of scrip receives - this is manually maintained
        # Columns: date, ticker, vol
        return
