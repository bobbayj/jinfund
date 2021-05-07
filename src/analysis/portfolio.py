from pathlib import Path
import pandas as pd
import numpy as np

DATA_DIR = Path(__file__).parent.parent / 'transactions'

def build():
    pickles = sorted(list(DATA_DIR.glob('*.pkl')))
    
    frames = [ pd.read_pickle(pickle) for pickle in pickles ]

    return pd.concat(frames)