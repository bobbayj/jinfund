from pathlib import Path
import pandas as pd

# Top-level directories -- will need to update when generalising
BASE_DIR = Path
BASE_DIR = Path.cwd().resolve().parent.parent # Needs update when moved to file
INPUT_DIR = Path.joinpath(BASE_DIR,'data') # Input dir path

## READ CSV FILE --> convert to function later
# This could also be generalised to any broker in future
csvfiles = sorted(list(INPUT_DIR.glob('commsec*')))
try: latest_csv = csvfiles[-1]
except IndexError:
    raise IndexError(f'No trade files from Commsec')

## Read file and return as dataframe
raw_df = pd.read_csv(latest_csv)

# Specific to commsec: filter for trades only
filtered_df = raw_df.loc[raw_df['Details'].str.startswith("B") | raw_df['Details'].str.startswith("S")]

# Specific to commsec: split out trade details
tx_df = filtered_df[['Date','Debit($)','Credit($)']]
    
# Note: Dataframe copy warning is fine, no values being written
tx_df[['Type','Volume','Ticker','Drop','Price']] = filtered_df['Details'].str.split(expand = True)
cols = ['Volume', 'Price']
tx_df[cols] = tx_df[cols].apply(pd.to_numeric, downcast='float')

# Clean dataframe --> Update data types, calculate final columns, drop useless columns, set index as date
tx_df['TradeValue'] = tx_df.fillna(0)['Debit($)'] + tx_df.fillna(0)['Credit($)']
tx_df['PriceIncBrokerage'] = tx_df['TradeValue'] / tx_df['Volume']
tx_df = tx_df.drop(columns=['Drop','Debit($)','Credit($)'])
tx_df['Date'] = pd.to_datetime(tx_df['Date'], dayfirst=True)
tx_df = tx_df.set_index('Date')

# Store output for other modules --> pickle is fine as raw is in .csv and will be used in Python only
# For future reference: https://towardsdatascience.com/stop-persisting-pandas-data-frames-in-csvs-f369a6440af5
tx_df.to_pickle(f"{latest_csv.with_suffix('.pkl')}")