from pathlib import Path
import pandas as pd
import numpy as np

DATA_DIR = Path(__file__).parent.parent / 'transactions'

def transactions():
    pickles = sorted(list(DATA_DIR.glob('*.pkl')))
    
    frames = [ pd.read_pickle(pickle) for pickle in pickles ]

    return pd.concat(frames)

def history(current=False):
    txs_df = transactions()
    txs_df['Value'] = txs_df['Volume'] * txs_df['PriceIncBrokerage']
    portfolio_dict = dict.fromkeys(txs_df['Ticker'].unique())

    for ticker in portfolio_dict.keys():
        value = txs_df[txs_df['Ticker'] == ticker]['Value'].cumsum().tolist()[-1]
        volume = txs_df[txs_df['Ticker'] == ticker]['Volume'].cumsum().tolist()[-1]
        cash_ins = txs_df[(txs_df['Ticker'] == ticker) & (txs_df['Type'] == 'B')]['Value'].cumsum().tolist()
        cash_outs = txs_df[(txs_df['Ticker'] == ticker) & (txs_df['Type'] == 'S')]['Value'].cumsum().tolist()
        
        portfolio_dict[ticker] = {
            'Value':                value,
            'Cash in':              cash_ins[-1],
            'Cash out':             cash_outs[-1] if len(cash_outs) > 0 else 0,
            'Volume':               volume,
            'PriceIncBrokerage':    value/volume if volume > 0 else np.nan,
        }

    portfolio_df = pd.DataFrame.from_dict(portfolio_dict, orient='index')
    
    if current:
      portfolio_df = portfolio_df[portfolio_df['Volume'] > 0]
      
    return portfolio_df.sort_index()


