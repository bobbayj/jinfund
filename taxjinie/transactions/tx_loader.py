from pathlib import Path
import pandas as pd
import numpy as np

DATA_DIR = Path(__file__).parent.parent / 'transactions'

class Loader():
    '''Reads txs and pickles them for later use

    Raises:
        IndexError: When no files are available from the broker
    '''
    def __init__(self):
        # self.broker = broker  # Use in future

        # Internal props
        self.raw_files = {}
        self.pkl_path = ''
        self.broker_dfs = {}
    
    def build(self):
        self.broker_dfs['commsec'] = self.commsec()

        master_tx_df = pd.DataFrame()
        for broker in self.broker_dfs:
            master_tx_df = pd.concat([master_tx_df, self.broker_dfs[broker]])

        dividends_df = self.scrip_dividends()
        dividends_df = dividends_df[master_tx_df.columns]

        master_tx_df = pd.concat([master_tx_df, dividends_df])
        master_tx_df = self.clean_df(master_tx_df)

        # Store output for other modules --> pickle is fine as raw is in .csv and will be used in Python only
        # For future reference: https://towardsdatascience.com/stop-persisting-pandas-data-frames-in-csvs-f369a6440af5
        fpath = DATA_DIR / 'portfolio'
        self.pkl_path = fpath.with_suffix('.pkl')
        master_tx_df.to_pickle(f"{self.pkl_path}")
    
    def commsec(self):
        # need a builder factory
        raw_df, self.raw_files['commsec'] = self.read_txs('commsec', 'csv')

        filtered_df = raw_df.loc[raw_df['Details'].str.startswith("B") | raw_df['Details'].str.startswith("S")]

        tx_df = filtered_df[['Date','Debit($)','Credit($)']]
            
        # Note: Dataframe copy warning is fine, no values being written
        tx_df[['Type','Volume','Ticker','Drop','Price']] = filtered_df['Details'].str.split(expand = True)
        cols = ['Volume', 'Price']
        tx_df[cols] = tx_df[cols].apply(pd.to_numeric, downcast='float')

        return tx_df

    def clean_df(self, tx_df):
        # Clean dataframe --> Update data types, calculate final columns, drop useless columns, set index as date
        tx_df['txValue'] = tx_df.fillna(0)['Debit($)'] + tx_df.fillna(0)['Credit($)']
        tx_df['PriceIncBrokerage'] = np.abs( tx_df['txValue'] / tx_df['Volume'] )
        tx_df['Brokerage'] = np.round(
            np.abs(
                tx_df['Volume'] * (tx_df['Price'] - tx_df['PriceIncBrokerage'])
                ),
            decimals = 2
            )
        tx_df['Volume'] = np.where(
            tx_df['Type'] == 'B'
            , tx_df['Volume']
            , -1 * tx_df['Volume']
        )
        tx_df = tx_df.drop(columns=['Drop','Debit($)','Credit($)', 'txValue'])
        tx_df['Date'] = pd.to_datetime(tx_df['Date'], dayfirst=True)
        tx_df = tx_df.set_index('Date')
        tx_df = tx_df.sort_values(['Date','Volume'],ascending=[True,False])  # Must ensure buys sorted on top for intra-day trades

        return tx_df
    
    def read_txs(self,broker, filetype='csv'):
        ## READ CSV FILE --> convert to function later
        # This could also be generalised to any broker in future
        csvfiles = sorted(list(DATA_DIR.glob(f'{broker}*{filetype}')))
        try: latest_csv = csvfiles[-1]
        except IndexError:
            raise IndexError(f'No tx files from {broker}')

        ## Read file and return as dataframe
        return (pd.read_csv(latest_csv), latest_csv)
    
    def scrip_dividends(self):
        raw_df, self.raw_files['dividends'] = self.read_txs('dividends', 'csv')

        temp_df = raw_df[raw_df['scrip_vol'].isna() == False]

        # Match columns
        temp_df = temp_df.rename(columns={
            'date': 'Date'
            ,'ticker': 'Ticker'
            ,'scrip_vol':'Volume'
            ,'scrip_price':'Price'
        })
        temp_df['Market'] = 'ASX'
        temp_df['PriceIncBrokerage'] = temp_df['Price']
        temp_df['Type'] = 'B'
        
        # Adding columns to align with broker
        temp_df['Credit($)'] = 0
        temp_df['Debit($)'] = 0
        temp_df['Drop'] = ''

        return temp_df