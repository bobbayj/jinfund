import pandas as pd
from pathlib import Path

# Local imports
from . import portfolio

class Performance():
  def __init__(self) -> None:
    self.txs = portfolio.transactions()
    self.calculate_tx_cashflows()
  
  def calculate_tx_cashflows(self):
    # Group transactions into months
    self.txs['CashflowIncBrokerage'] = self.txs['Volume'] * self.txs['PriceIncBrokerage']
    self.txs['Cashflow'] = self.txs['Volume'] * self.txs['Price']
  
  def _ticker_monthly_cashflows(self, ticker):
    ticker_df = self.txs[self.txs['Ticker'] == ticker]
    ticker_df = ticker_df.groupby(pd.Grouper(freq='M')).sum()
    ticker_df = ticker_df.set_index(ticker_df.index.values.astype('datetime64[M]'))
    
    ticker_df['Ticker'] = ticker
    ticker_series = ticker_df['Ticker']
    ticker_df = ticker_df.drop(columns=['Ticker'])
    ticker_df.insert(loc=0, column='Ticker', value=ticker_series)
    
    return ticker_df[ticker_df['Volume'] != 0]

  def monthly_cashflows(self, ticker:str='portfolio', export=False):
    ticker_df = pd.DataFrame()

    if ticker == 'portfolio':
      for looped_ticker in self.txs['Ticker'].unique():
        ticker_df = pd.concat([ticker_df, self._ticker_monthly_cashflows(looped_ticker)])

    else:
      ticker_df = pd.concat([ticker_df, self._ticker_monthly_cashflows(ticker)])

    if export:
      last_month = ticker_df.last_valid_index()
      fname = f'monthly_cashflows_{last_month:%Y%m%d}'
      fpath = Path(__file__).parent.parent / 'reports' / fname
      ticker_df.to_excel(fpath.with_suffix('.xlsx'))

      print(f'Saved!\n\tFilename:\t{fpath.name}\n\tOutput path:\t{fpath}')

    return ticker_df
