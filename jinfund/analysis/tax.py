# Standard imports
import pandas as pd
from pathlib import Path
from datetime import datetime

# Local imports
from ..portfolio.transactions import Transactions

class AutoTax():
    '''Automatically calculates capital gains tax over a specified period for one or all stocks using trade and scrip dividend data.
    
    Functions:
        fy_view(yr_end = None, summary = True) -- Provides a snapshot of capital gains for period. Defaults to current FY
    '''
    output_path = Path.cwd()/('output')

    def __init__(self, financial_year:int=2020):
        self.cgt_log = CGTLog()
        self.tx_df = Transactions().tx_df
        self.tickers = list(sorted(set(self.tx_df.reset_index().Ticker.to_list())))
        self.__finyear = financial_year
        self.__fystart = self.finyear - 1
        self.cgt_df = self.__build_from_transactions()

    @property
    def finyear(self):
        today = datetime.today()
        self.__finyear = today.year
        if today.month > 6:
            self.__finyear += 1
        return self.__finyear
    
    @finyear.setter
    def finyear(self, value:int):
        if value < 2015: raise ValueError('Year out of bonds. Must be 2015 or after.')
        self.__finyear = value
    
    @property
    def fystart(self):
        self.__fystart = self.finyear - 1
        return self.__fystart

    
    def __build_from_transactions(self):    
        '''Constructs capital gains for all trades
        
        Returns:
            DataFrame -- of capital gains for all tickers. MultiIndex: (Date, Ticker), Column: [CapitalGain]
        '''        
        
        capital_gains = pd.DataFrame()  # Initalise empty df

        for ticker in self.tickers:
            tick_cg_df = self.__ticker_cgt_events(ticker)
            if len(tick_cg_df) > 0:
                capital_gains = tick_cg_df if len(capital_gains)==0 else pd.concat([capital_gains,tick_cg_df])

        return capital_gains.set_index('Date').sort_index()

    def __ticker_cgt_events(self, ticker):
        '''Analyses CGT events based off LIFO logic
        
        Arguments:
            ticker {string} -- Stock ticker to analyse. Must be in transaction history
        
        Returns:
            DataFrame -- Columns: [Ticker, Date, CapitalGain]
        '''                
        # LIFO tax logic...tends to minimise tax on average due to lower CG
        # LIFO = last-in, first-out. Most recently purchased  volume is the first to be sold
        
        ticker_df = self.tx_df.xs(ticker,level=1,axis=0).sort_values(['Date','Volume'],ascending=[True,False])  # Must ensure buys sorted on top for intra-day trades
        dates = list(ticker_df.index)
        txs = ticker_df.to_dict('list')
        buy_queue = []
        cgt_events=  []

        for i, date in enumerate(dates):
            tx_dict = {
                'Date': date,
                'Volume': txs['Volume'][i],
                'TradePrice': txs['TradePrice'][i],
                'EffectivePrice': txs['EffectivePrice'][i],
                'Brokerage': txs['Brokerage'][i],
            }
            tx_vol = tx_dict['Volume']  # Simpler to read
            tx_cg, tx_cg_taxable = 0, 0  # Reset to 0 for each new tx

            if tx_vol > 0:  # Buys in queue
                buy_queue.append(tx_dict)
            else:  # Sells reduced by
                buy_logs = []                                       # Flush buy logs
                while tx_vol != 0:                                  # Loop until all the sold volume is accounted for
                    if buy_queue[-1]['Volume'] == 0:                # Catch any 0 volume buy parcels
                        buy_parcel = buy_queue.pop()
                        continue
                    elif abs(tx_vol) < buy_queue[-1]['Volume']:     # Sell volume is less than or equal to previous buy volume
                        cg, cg_taxable, buy_queue[-1] = self.__cg_calc(buy_queue[-1], tx_dict, limiter='sell')
                        buy_log = buy_queue[-1].copy()              # For logging - initial shares in buy_parcel
                        buy_queue[-1]['Volume'] += tx_vol           # Reduce LIFO buy_volume by sale_volume (sale_volume is negative)
                        tx_vol = 0
                    else:                                           # Sell volume greater than previous buy volume
                        buy_parcel = buy_queue.pop()                # Remove buy_parcel from buy_queue as it has been depleted
                        cg, cg_taxable, buy_parcel = self.__cg_calc(buy_parcel, tx_dict, limiter='buy')
                        buy_log = buy_parcel.copy()                 # For logging - remaining shares in buy_parcel
                        tx_vol += buy_parcel['Volume']              # Increase sale_volume by LIFO buy_volume (sale_volume is negative)
                    tx_cg += cg
                    tx_cg_taxable += cg_taxable
                    buy_logs.append(buy_log)                        # Keep log of buys associated with sale

                cgt_detailed_log = { # Log event for reporting
                    'ticker': ticker,
                    'date': date,
                    'volume': txs['Volume'][i],
                    'cg': tx_cg,
                    'cgt': tx_cg_taxable,
                    'buy_parcels': buy_logs,                        # Note: brokerage value is pre-CGT event pro-rating and deduction
                    'sell_parcel': tx_dict,
                }
                self.cgt_log.record(cgt_detailed_log)

                cgt_event = {  # Dict to store capital gain event
                    'Ticker': ticker,
                    'Date': date,
                    'CapitalGains': tx_cg,
                    'CapitalGainsTaxable': tx_cg_taxable,
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
        limiter_options = ['buy','sell']
        if limiter not in limiter_options:
            raise ValueError(f'Invalid partial type. Expected one of: {limiter_options}')
        if limiter == 'buy':  # More buy volume than sell volume
            volume = buy_parcel['Volume']
        else:  # More sell volume than buy volume
            volume = abs(sell_parcel['Volume'])
        
        # Brokerage pro-rata calculation
        pr_factor = volume/buy_parcel['Volume'] if volume/buy_parcel['Volume'] < 1 else 1
        buy_brokerage = buy_parcel['Brokerage'] * pr_factor  # Pro-rate buy brokerage as less is sold from this parcel
        buy_parcel['Pro-rate_brokerage'] = buy_brokerage  # Pro-rated amount of brokerage for this transaction
        buy_parcel['Brokerage'] -= buy_brokerage  # Remaining brokerage for buy_parcel

        buy_value = volume * buy_parcel['TradePrice']
        sell_value = volume * sell_parcel['TradePrice']

        cg = sell_value - buy_value
        if ((sell_parcel['Date'] - buy_parcel['Date']).days > 365) and (cg > 0):
            cg_taxable = cg / 2 # Apply any capital gains discounts if applicable
        else:
            cg_taxable = cg
        cg_taxable -= (buy_brokerage + sell_parcel['Brokerage'])  # Brokerage is tax deductible
        
        return cg, cg_taxable, buy_parcel

    def fy_view(self, summary = True):
        '''Returns view of capital gains for the given financial year.
        
        Keyword Arguments:
            summary {bool} -- Summarises capital gains per ticker. Set to False for date details (default: {True})
        
        Returns:
            DataFrame -- View of capital gains
        '''
        fy_df = self.cgt_df.loc[f'{self.fystart}-07-01':f'{self.finyear}-06-30']

        if summary:
            fy_df = fy_df.groupby('Ticker').sum()
        
        print(f'''
Capital gains for \tFY{self.fystart}-{self.finyear}
Total CG:\t\t ${fy_df['CapitalGains'].sum(): .2f}
Total CGTaxable:\t ${fy_df['CapitalGainsTaxable'].sum(): .2f}
(Uses LIFO method)
        ''')
        return fy_df

    def cgt_report(self, to_csv:bool=True):
        '''Creates a .csv report of all capital gains events for the given year and the parcels involved
        '''
        df = pd.DataFrame(self.cgt_log.log).set_index('date')  # Dependent on how the data is logged in AutoTax!
        df['buys_associated'] = df.apply(lambda x: len(x['buy_parcels']), axis=1)
        fy_df = df.loc[f'{self.fystart}-07-01':f'{self.finyear}-06-30']
        
        fname = f'FY{self.finyear}_cgt_report.csv'
        if to_csv: self.__export_df_to_csv(fy_df,fname)

        return fy_df

    def cgt_details(self, ticker:str=None, show_all:bool=True, to_csv:bool=True):
        
        combined_df = pd.DataFrame()

        if show_all:  # Combine all ticker_dfs
            for ticker in self.tickers:
                ticker_df = self.__ticker_detail(ticker=ticker)
                combined_df = pd.concat([combined_df, ticker_df])
            fname = 'cgt_details_all.csv'
        elif ticker is None:
            raise ValueError(f'No ticker selected. Set <show_all> to True\n or set <ticker> to one of the following:\n{self.tickers}')
        else:
            combined_df = self.__ticker_detail(ticker=ticker)
            fname = f'cgt_details_{ticker}.csv'
        
        fy_df = combined_df.loc[f'{self.fystart}-07-01':f'{self.finyear}-06-30']
        if to_csv: self.__export_df_to_csv(fy_df,fname)

        return fy_df
    
    def __ticker_detail(self, ticker:str=None):
        df = pd.DataFrame(self.cgt_log.log).set_index('date')
        temp = df.loc[df['ticker']==ticker][['buy_parcels','sell_parcel']].to_dict('series')
        if len(temp['sell_parcel']) == 0:
            return pd.DataFrame()  # Return empty dataframe

        buys, sells = pd.DataFrame(), pd.DataFrame()
        for buy, sell in zip(temp['buy_parcels'],temp['sell_parcel']):
            sells = pd.concat([sells,pd.DataFrame([sell])],join='outer')
            buys = pd.concat([buys,pd.DataFrame(buy)],join='outer')

        sells['Type'] = 'Sells'
        buys['Type'] = 'Buys'
        ticker_df = pd.concat([sells,buys])
        ticker_df['Ticker'] = ticker
        ticker_df = ticker_df.set_index(['Ticker','Type','Date'])

        return ticker_df.sort_values(['Date','Volume'],ascending=[True,False])
    
    def __export_df_to_csv(self, df:pd.core.frame.DataFrame, fname:str):
        fpath = self.output_path / fname
        df.to_csv(fpath)
        print(f'Saved to csv!\n\tFilename:\t{fname}\n\tOutput path:\t{self.output_path}')

class CGTLog():
    def __init__(self):
        self.log = []

    def record(self, cgt_logdict):
        return self.log.append(cgt_logdict)


    @property
    def view(self):
        return self.log