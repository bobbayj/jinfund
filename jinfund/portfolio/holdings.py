# System imports
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# Third-party imports
from pathlib import Path
import yfinance as yf

# Local imports
from portfolio.commsec import Trades
import datehandler


class Portfolio:
    def __init__(self):
        '''View portfolio data and returns
        '''
        # Dates and file paths
        self.today = datetime.today()
        self.save_dir = Path(__file__).parents[1] / 'data'
        self.portfolio_csv_name = f'portfolio_holdings.csv'
        self.portfolio_csv_path = self.save_dir / self.portfolio_csv_name
        
        # Create portfolio from trades
        self.holdings = self.build()

    def build(self):
        # Initialise transaction data and get trades
        trades = Trades()
        trades_df = trades.all

        # Construct range of dates over portfolio period
        p_inception = trades_df.index[0][0]
        p_dates = datehandler.date_list(p_inception, self.today)

        # Create base dataframe
        df_base_dates = pd.DataFrame(index=p_dates)
        df_base_dates.index.name = 'Date'

        df_pfolio = pd.DataFrame()  # Initialise the main portfolio df as empty

        # Build list of tickers seen throughout investment period
        tickers = list(sorted(set(trades_df.reset_index().Ticker.to_list())))

        # Use yfinance to get close prices
        lookup_tickers = [f'{ticker}.AX' for ticker in tickers]  # Only supports ASX stocks
        lookup_tickers = ' '.join(lookup_tickers)

        prices = yf.download(lookup_tickers, start=p_dates[0], end=p_dates[-1])
        close = prices['Adj Close'] # Using Adj Close instead of Close to account for stocksplits, dividends
        close.columns = tickers

        # Step through transactions dataframe, ticker by ticker
        for ticker in tickers:
            vol_df = trades.by_ticker(ticker)['Volume']  # Get volumes

            # Merge with base_dates_df and cumulative sum the volumes
            ticker_df = pd.merge_ordered(vol_df, df_base_dates, on='Date').set_index('Date')
            ticker_df = ticker_df.cumsum().ffill()
            ticker_df = ticker_df[ticker_df['Volume'].isna() == False]

            # Merge with close prices
            ticker_df = pd.merge_ordered(ticker_df, close[ticker], on='Date').set_index('Date')
            ticker_df.rename({ticker: 'Close'}, axis=1, inplace=True)
            
            # Merge ticker_df with portfolio_df
            ticker_df['Ticker'] = ticker # create ticker column for later indexing
            df_pfolio = pd.concat([df_pfolio, ticker_df])

        df_pfolio = df_pfolio.reset_index().set_index(['Date','Ticker']).sort_index() # Finalise portfolio

        return df_pfolio
    
    def 