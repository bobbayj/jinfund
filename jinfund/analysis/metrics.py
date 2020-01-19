# Standard imports
import pandas as pd

# 3rd party imports

# Local imports


def time_weighted_average_return(df, start_date=None, end_date=None):
    # twar = time_weighted_average_return
    if start_date is None:
        start_date = df.index[-1]
    if end_date is None:
        end_date = df.index[0]

    # Numerator: End value - (initial value + cashflow)
    # Denominator: Initial value + cashflow
    
    # Cashflow
        # cash dividends --> from df
        # Buying / selling stocks --> from transactions

    twar = 0


    return twar




