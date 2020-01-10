'''
Reads and prepares Commsec transactions.csv files

Note that transactions only show on the T+2 date
'''
import csv
import pandas as pd
import numpy as np
from pathlib import Path

# Structure as Class object
class Trades:
    def __init__(self):
        dirname =  Path(__file__).parents[0]
        csvfiles = sorted(list(dirname.glob('*csv')))
        latest_csv = csvfiles[-1]

        tx_df = pd.read_csv(latest_csv)
        tx_df = self.digest_txs(tx_df)

        self.tx_df = tx_df

    def digest_txs(self,df):
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
        temp_df.columns = ['TradeType','Volume','AsxCode','TradePrice']
        df = df.join(temp_df)
        
        # Change str to float
        df['Volume'] = pd.to_numeric(df['Volume'], downcast='float')
        df['TradePrice'] = pd.to_numeric(df['TradePrice'], downcast='float')

        # Calculate effective price inclusive of brokerage
        df['Debit($)'].fillna(df['Credit($)'], inplace=True)
        df['EffectivePrice'] = df['Debit($)'] / df['Volume']

        # Calculate brokerage
        df['Brokerage'] = df['Volume']*(df['EffectivePrice'] - df['TradePrice'])
        df['Brokerage'] = np.round(np.abs(df['Brokerage']),decimals=0)

        # Clean df for export
        cols = ['Date','AsxCode','TradeType','Volume','TradePrice','EffectivePrice','Brokerage']
        df = df[cols]
        df = df.set_index('Date')

        return df
    
    def all(self):
        return self.tx_df
    
    def buys(self):
        df = self.tx_df[self.tx_df.TradeType == 'B']
        return df

    def sells(self):
        df = self.tx_df[self.tx_df.TradeType == 'S']
        return df
