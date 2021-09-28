import pandas as pd
from datetime import datetime

# Local imports
from . import portfolio

class Performance():
  def __init__(self) -> None:
    self.txs = portfolio.transactions()
    self.cashflows = self.calculate_cashflows()
    
    inception_date = self.transactions.first_valid_index().date()
    latest_month = datetime.today().date()
    portfolio_months = pd.date_range(start=inception_date, end=latest_month, freq='MS')
    self.monthly_dataframe = pd.DataFrame(portfolio_months, columns=['Month']).set_index('Month')
  
  def calculate_cashflows(self):
    # Group transactions into months
    self.txs['CashflowIncBrokerage'] = self.txs['Volume'] * self.txs['PriceIncBrokerage']
    self.txs['Cashflow'] = self.txs['Volume'] * self.txs['Price']
  
  def ticker_monthly_summary(self, ticker:str):
    ticker_df = self.txs[self.txs['Ticker'] == ticker]
    ticker_df = ticker_df.groupby(pd.Grouper(freq='M')).sum()
    
    return ticker_df[ticker_df['Volume'] != 0]

  def money_weight_return(self, ticker:str='portfolio'):
    ticker_df = pd.DataFrame()

    if ticker == 'portfolio':
      for ticker in self.txs['Ticker'].unique():
        ticker_df.append(self.ticker_monthly_summary(ticker))

    else:
      ticker_df.append(self.ticker_monthly_summary(ticker))


