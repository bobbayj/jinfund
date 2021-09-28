from pathlib import Path
import pandas as pd
from datetime import datetime
import textwrap

# Local imports
from . import portfolio

class Tax():
    def __init__(self, financial_year:int=2021) -> None:
        self.transactions = portfolio.transactions()
        self.cgt_log = []
        self.all_cg_events = pd.DataFrame()

        self.__fy_end = financial_year
        self.__fy_start = self.fy_end - 1

    @property
    def fy_end(self):
        return self.__fy_end
    
    @fy_end.setter
    def fy_end(self, value:int):
        today = datetime.today()
        if self.__fy_end == 0:
            self.__fy_end = today.year
            if today.month > 6:
                self.__fy_end += 1
        if value < 2015: raise ValueError('Year out of bonds. Must be 2015 or after.')
        self.__fy_end = value
    
    @property
    def fy_start(self):
        self.__fy_start = self.fy_end - 1
        return self.__fy_start
    
    def capital_gain_events(self):
        '''Loops through and calculates capital gains for each ticker
        '''
        for ticker in self.transactions['Ticker'].unique():
            ticker_capital_gain_events = self.__ticker_cg(ticker)
            if len(ticker_capital_gain_events) > 0:
                self.all_cg_events = pd.concat([self.all_cg_events,ticker_capital_gain_events])
        
        self.all_cg_events = self.all_cg_events.set_index('Date').sort_index()

    def __ticker_cg(self, ticker):
        '''Calculates capital gains using Last in, first out logic
        '''
        tx_df = self.transactions[self.transactions['Ticker'] == ticker]
        dates = list(tx_df.index)

        txs = tx_df.to_dict('list')     # For easier sequential access to each row
        buy_queue = []                  # Flush for new ticker
        cgt_events=  []                 # Flush for new ticker

        for i, date in enumerate(dates):
            tx_dict = {
                'Ticker': ticker,
                'Date': date,
                'Volume': txs['Volume'][i],
                'Price': txs['Price'][i],
                'PriceIncBrokerage': txs['PriceIncBrokerage'][i],
                'Brokerage': txs['Brokerage'][i],
            }
            tx_vol = tx_dict['Volume']  # Simpler to read
            tx_cg, tx_cg_taxable = 0, 0  # Reset to 0 for each new tx

            if tx_vol > 0:  # Buys in queue
                buy_queue.append(tx_dict)
            else:  # Sells reduced by
                buy_logs = []                                       # Flush buy logs
                
                while tx_vol != 0:                                  # Loop until all the sold volume is accounted for
                    try:
                        type(buy_queue[-1])                         # Check for any missing buy transactions
                    except IndexError as err:
                        raise(f'{err}: There is a missing buy transaction for {ticker}, with volume: {abs(tx_vol)}')

                    if buy_queue[-1]['Volume'] == 0:                # Catch any 0 volume buy parcels
                        buy_parcel = buy_queue.pop()
                        continue
                    elif abs(tx_vol) < buy_queue[-1]['Volume']:     # Sell volume is less than or equal to previous buy volume
                        cg, cg_taxable = self.__cg_calc(buy_queue[-1], tx_dict, limiter='sell')
                        buy_log = buy_queue[-1].copy()              # For logging - initial shares in buy_parcel
                        buy_queue[-1]['Volume'] += tx_vol           # Reduce LIFO buy_volume by sale_volume (sale_volume is negative)
                        tx_vol = 0
                    else:                                           # Sell volume greater than previous buy volume
                        buy_parcel = buy_queue.pop()                # Remove buy_parcel from buy_queue as it has been depleted
                        cg, cg_taxable = self.__cg_calc(buy_parcel, tx_dict, limiter='buy')
                        buy_log = buy_parcel.copy()                 # For logging - remaining shares in buy_parcel
                        tx_vol += buy_parcel['Volume']              # Increase sale_volume by LIFO buy_volume (sale_volume is negative)
                    
                    tx_cg += cg
                    tx_cg_taxable += cg_taxable
                    buy_logs.append(buy_log)                        # Keep log of buys associated with sale

                cgt_detailed_log = { # Log event for reporting
                    'Ticker': ticker,
                    'Date': date,
                    'Volume': txs['Volume'][i],
                    'Capital Gains': tx_cg,
                    'Capital Gains Taxable': tx_cg_taxable,
                    'Buy Parcels': buy_logs,
                    'Sell Parcel': tx_dict,
                }
                self.cgt_log.append(cgt_detailed_log)

                cgt_event = {  # Dict to store capital gain event
                    'Ticker': ticker,
                    'Date': date,
                    'Capital Gains': tx_cg,
                    'Capital Gains Taxable': tx_cg_taxable,
                    }
                cgt_events.append(cgt_event)

        return pd.DataFrame(cgt_events)
    
    def __cg_calc(self, buy_parcel, sell_parcel, limiter='buy'):  # Aux function
        '''Calculates capital gains given buy and sell parcels, using the the buy or sell volume. Considers brokerage as tax deductible
        
        Arguments:
            buy_parcel {dict} -- Requires keys: [Date, Volume, TradePrice, Brokerage]
            sell_parcel {dict} -- Requires keys: [Date, Volume, TradePrice, Brokerage]
            limiter {string} -- ['buy','sell']; Defines the buy or sell volume as the limiting volume for the calculation
        Returns:
            float -- calculated capital gains
        '''
        if limiter not in ['buy','sell']:
            raise ValueError(f'Invalid partial type. Expected one of: ["buy","sell"]')
        if limiter == 'buy':  # More buy volume than sell volume
            volume = buy_parcel['Volume']
        else:  # More sell volume than buy volume
            volume = abs(sell_parcel['Volume'])

        buy_value = volume * buy_parcel['PriceIncBrokerage']  # PriceIncBrokerage incldues brokerage
        sell_value = volume * sell_parcel['PriceIncBrokerage']  # PriceIncBrokerage incldues brokerage

        cg = sell_value - buy_value
        if ((sell_parcel['Date'] - buy_parcel['Date']).days > 365) and (cg > 0):
            cg_taxable = cg / 2 # Apply any capital gains discounts if applicable
        else:
            cg_taxable = cg
        
        return cg, cg_taxable

    def fy_view(self, summary = True):
        '''Returns view of capital gains for the given financial year.
        
        Keyword Arguments:
            summary {bool} -- Summarises capital gains per ticker. Set to False for date details (default: {True})
        
        Returns:
            DataFrame -- View of capital gains
        '''
        fy_df = self.all_cg_events.loc[f'{self.fy_start}-07-01':f'{self.fy_end}-06-30']

        if summary:
            fy_df = fy_df.groupby('Ticker').sum()
        
        log_message = textwrap.dedent(f'''\
          Capital gains for \tFY{self.fy_start}-{self.fy_end}
          Total CG:\t\t ${fy_df['Capital Gains'].sum(): .2f}
          Total CGTaxable:\t ${fy_df['Capital Gains Taxable'].sum(): .2f}
          (Uses LIFO method)
        ''')
        print(log_message)

        return fy_df

    def cgt_report(self, output_type='csv'):
        '''Creates a .csv report of all capital gains events for the given year and the parcels involved

        Args:
            output_type (str, optional): Select output type, `excel` or `csv`. Defaults to 'csv'.

        Returns:
            pandas.DataFrame: CGT log for the selected financial year
        '''
        df = pd.DataFrame(self.cgt_log).set_index('Date').sort_index()  # Dependent on how the data is logged in AutoTax!
        df['Buys Associated'] = df.apply(lambda x: len(x['Buy Parcels']), axis=1)
        fy_df = df.loc[f'{self.fy_start}-07-01':f'{self.fy_end}-06-30']
        
        fname = f'FY{self.fy_end}_cgt_report.csv'
        if output_type == 'excel': self.__export_df_to_csv(fy_df,fname, excel = True)
        else: self.__export_df_to_csv(fy_df,fname, excel = False)

        return fy_df

    def upcoming_cgtdiscounts(self):
      today = datetime.today()
      pastyear_df = self.transactions.loc[today - pd.DateOffset(years=1) : today]
      buy_parcels_list = []

      for ticker in pastyear_df['Ticker'].unique():

        ticker_df = pastyear_df[ pastyear_df['Ticker'] == ticker]
        tx_list = ticker_df.reset_index().to_dict("records")
        buy_parcels_ticker = []

        for tx in tx_list:
          if tx['Type'] == 'B':
            buy_parcels_ticker.append(tx)

          else:
            try:
              buy_parcels_ticker[-1]['Volume'] -= - tx['Volume']

            except IndexError:
              print(f'>> No buys for sale of {ticker} in past year <<')
              continue
        
          # Only include buy parcels that have not been closed
          if buy_parcels_ticker:
            while buy_parcels_ticker[-1]['Volume'] <= 0:
              try:
                buy_parcels_ticker[-2]['Volume'] -= buy_parcels_ticker[-1]['Volume']
                print(buy_parcels_ticker)
                buy_parcels_ticker.pop()
              
              except IndexError:
                print(f'>> {ticker} has been sold for this parcel <<')
                buy_parcels_ticker.pop()
                break
              
          
        buy_parcels_list.append(buy_parcels_ticker)

      buy_parcels_list = self.flatten(buy_parcels_list)

      cgt_upcoming_df = pd.DataFrame(buy_parcels_list).set_index('Date')
      cgt_upcoming_df['CGT Discount Date'] = cgt_upcoming_df.index + pd.DateOffset(years = 1)

      self.__export_df_to_csv(
        cgt_upcoming_df
        , fname=f'upcoming_cgt_discounts_{today:%Y%m%d}'
        , excel=True
        )

    def __export_df_to_csv(self, df, fname:str, excel=False):
        fpath = Path(__file__).parent.parent / 'reports' / fname
        if excel:
            fpath = fpath.with_suffix('.xlsx')
            df.to_excel(fpath.with_suffix('.xlsx'))
        else:
            df.to_csv(fpath.with_suffix('.csv'))

        print(f'Saved!\n\tFilename:\t{fpath.name}\n\tOutput path:\t{fpath}')

    def export_tx_history(self):
        fname = f'transaction_history_{datetime.today():%Y%m%d}'

        self.__export_df_to_csv(portfolio.current(), fname, excel=True)

    def flatten(self, t):
      return [item for sublist in t for item in sublist]
