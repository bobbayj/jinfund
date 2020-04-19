# System imports
import csv
import pandas as pd
import numpy as np
from pathlib import Path

# Define data source path
dirname = Path(__file__).parents[1] / 'data'

class Trades:
    '''
    Reads and prepares Commsec transactions.csv files

    Note that transactions only show on the T+2 date
    '''
    def __init__(self,broker):
        try:
            csvfiles = sorted(list(dirname.glob(f'{broker}*')))
        except:
            return
        latest_csv = csvfiles[-1]

        t_df = pd.read_csv(latest_csv)

        if broker == 'commsec':
            self.t_df = self.digest_commsec(t_df)
        else:
            self.t_df = pd.DataFrame()

    def digest_commsec(self, df):
        """Digest raw transactions.csv dataframe
        
        EffectivePrice includes brokerage

        Arguments:
            df {Dataframe} -- Raw transactions.csv loaded into a dataframe
        """
        details = df['Details'].tolist()
        trades = []

        # Split details data
        for detail in details:
            if detail[0] in ['B','S']:  # Trades start with B or S
                detail = detail.split()
                for i,txt in enumerate(detail):
                    if txt == '@':
                        detail.pop(i)
            else:
                detail = np.nan  # Mark non-trade details as NaN
            trades.append(detail)

        # Keep only trade transactions
        df['Trades'] = trades
        df = df[df.Trades.notnull()]

        # Flatten list of trade data to columns
        temp_df = df.Trades.apply(pd.Series)
        temp_df.columns = ['TradeType','Volume','Ticker','TradePrice']
        df = df.join(temp_df)

        # Convert string dates to datetime via pandas
        df.Date = pd.to_datetime(df.Date, dayfirst=True)

        # Change str to float
        df['Volume'] = pd.to_numeric(df['Volume'], downcast='float')
        df['TradePrice'] = pd.to_numeric(df['TradePrice'], downcast='float')
        
        # Assign negative signs to volume if trades are sells
        df['Volume'] = np.where(df['TradeType']=='S', df['Volume']*-1,df['Volume'])

        # Calculate effective price inclusive of brokerage
        df['Debit($)'].fillna(df['Credit($)'], inplace=True)
        df['EffectivePrice'] = np.abs(df['Debit($)'] / df['Volume'])

        # Calculate brokerage
        df['Brokerage'] = df['Volume']*(df['EffectivePrice'] - df['TradePrice'])
        df['Brokerage'] = np.round(np.abs(df['Brokerage']),decimals=0)

        # Add market for all trades
        df['Market'] = 'ASX'

        # Clean df for export
        cols = ['Date','Ticker','Market','Volume','TradePrice','EffectivePrice','Brokerage']
        df = df[cols]
        df = df.set_index(['Date','Ticker'])
        df = df.sort_index()

        return df
    
    @property
    def all(self):
        '''
        Returns:
            Dataframe -- all transactions
        '''
        return self.t_df
    
    @property
    def buys(self):
        '''
        Returns:
            Dataframe -- only buy transactions
        '''        
        return self.t_df[self.t_df.TradeType == 'B']

    @property
    def sells(self):
        '''
        Returns:
            Dataframe -- only sell transactions
        '''        
        return self.t_df[self.t_df.TradeType == 'S']

    @property
    def cashflow(self):
        '''Returns a series for the change in cash balance
        
        Returns:
            Series -- cash per trade, indexed by portfolio dates
        '''
        df = pd.DataFrame(index=self.t_df.index)
        df['Type'] = np.where(self.t_df.TradeType == 'B', -1, 1)
        df['Value'] = self.t_df.Volume * self.t_df.EffectivePrice * df.Type
        df = df.drop(columns = 'Type')
        return df
    
    def by_ticker(self, ticker):
        return self.t_df.xs(ticker,level=1,axis=0)

    def by_date(self,date):
        return self.t_df.xs(date,level=0,axis=0)

class Dividends:
    def __init__(self):
        csvfiles = sorted(list(dirname.glob('divs*')))
        latest_csv = csvfiles[-1]

        d_df = pd.read_csv(latest_csv)
        d_df['date'] = pd.to_datetime(d_df['date'],dayfirst=True)  # Convert dates to datetime, and set multiindex [date, ticker]
        self.d_df = d_df.set_index(['date','ticker']).sort_index()
    
    @property
    def all(self):
        return self.d_df

class Transactions:
    '''Combines trades from brokers and manually-inputted dividends into one pd.DataFrame.
    Currently only supports Commsec trades
    
    Returns:
        pd.DataFrame -- Columns: Ticker | Market | TradePrice | EffectivePrice | Brokerage | Scrip
    '''

    brokers = ['commsec']

    def __init__(self):
        self.t_df = self.__collate_broker_trades()
        self.d_df = Dividends().all

        self.tx_df = self.__combine_trades_divs()

    def __collate_broker_trades(self):
        df = pd.DataFrame()
        for broker in Transactions.brokers:
            t = Trades(broker)
            df = df.append(t.all)
        return df.sort_index()

    def __combine_trades_divs(self):
        df = self.d_df
        # Get scrip dividends only
        temp_df = df[df['scrip_vol'].isna()==False]

        # Match columns
        temp_df = temp_df.rename(columns={'scrip_vol':'Volume','scrip_price':'TradePrice'})
        temp_df['Market'] = 'ASX'
        temp_df['EffectivePrice'] = temp_df['TradePrice']
        temp_df['Brokerage'] = 0
        temp_df = temp_df[self.t_df.columns]
        temp_df['Scrip'] = 1

        return pd.concat([self.t_df,temp_df],axis=0, join='outer').sort_index()  # Combine the dataframes together and return

    @property
    def cash_dividends(self):
        return self.d_df[self.d_df['cash']>0]['cash']