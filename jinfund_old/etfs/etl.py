# Standard library imports
import pandas as pd
import numpy as np
from datetime import datetime
from . import setup
import os
import csv

# Get variables from setup module
data_folder = setup.commonData().datafolder
country_dict = setup.commonData().countrydict()

# Vanguard ETL
def blackrock_etl(date):
    [urls, etfs] = setup.commonData().blackrock()

    # Get filenames of blackrock etf's
    csvfiles = []
    for dirname, dirnames, filenames in os.walk(data_folder):
        for filename in filenames:
            fpath = os.path.join(dirname, filename)

            for etf in etfs:
                if etf in fpath:
                    csvfiles.append(fpath)

    # Initiatve variables
    masterdf = pd.DataFrame()

    # Read csv's as dataframes and aggregate into a master
    for file in csvfiles:
        if date in file:
            with open(file, 'r', encoding='windows-1252') as f:
                data = csv.reader(f)
                data = list(data)

            # Find index positions of 'Ticker'
            Ticker_pos = []
            for i, e in enumerate(data):
                if 'Ticker' in e:
                    Ticker_pos.append(i)

            # Column titles begin where last index of 'Ticker' is located
            read_from_index = Ticker_pos[-1]
            cols = data[read_from_index]

            # 1st holding details are one row after the ticker row.
            # Make sure to exclude final 2 rows of disclaimers
            holdings = data[read_from_index+1:-2]

            df = pd.DataFrame(holdings, columns=cols)

            # Convert numbers stored as strings into float type
            cols_str2num = ['Weight (%)', 'Price', 'Shares',
                            'Market Value', 'Notional Value']
            for col in cols_str2num:
                df[col] = df[col].str.replace(',', '')
                df[col] = df[col].astype(float)

            # Add backsolved Weightings column
            df['Weighting'] = (df['Market Value']/df['Market Value'].sum())*100

            # Add date
            df.insert(0, 'Date', date)

            # Add etf symbol
            # Extract ETF name from filepath
            try:  # Windows file naming, referenced from the root
                etf = file.split('_')[0].split('\\')[3]
            except IndexError:  # Linux file naming, referenced from the root
                etf = file.split('_')[0].split('/')[3]
            finally:
                df.insert(1, 'etf', etf)

            # Append to masterdf
            masterdf = masterdf.append(df, ignore_index=True, sort=False)

    # Sort masterdf inplace
    masterdf.sort_values(['etf', 'Weighting'], inplace=True)

    return masterdf.reset_index()


# Vanguard ETL
def vanguard_etl(date):
    [urls, etfs] = setup.commonData().vanguard()
    # Get csvfiles and unique dates in folder
    csvfiles = []
    for dirname, dirnames, filenames in os.walk(data_folder):
        for filename in filenames:
            fpath = os.path.join(dirname, filename)

            for etf in etfs:
                if etf in fpath:
                    csvfiles.append(fpath)
    # Initiate variables
    masterdf = pd.DataFrame()

    # Aggregate each ETF into one dataframe - only keep columns defined
    for file in csvfiles:
        if date in file:  # Get the latest dates only
            df = pd.read_csv(file)

            # Calculate share of each holding in ETF
            df['Weighting'] = (df['marketValue']/df['marketValue'].sum())*100

            # If symbol is NaN, replace with holding
            df['symbol'].fillna(df['holding'], inplace=True)

            # Include column of etf name
            # Extract ETF name from filepath
            try:  # Windows file naming
                etf = file.split('_')[0].split('\\')[3]
            except IndexError:  # Linux file naming
                etf = file.split('_')[0].split('/')[3]
            finally:
                df.insert(1, 'etf', etf)

            # Append dataframe to master
            masterdf = masterdf.append(df, ignore_index=True, sort=False)

    # Intermediate aggregated dataframe...
    # symbols have not seen a final check with classification table
    masterdf.sort_values(['etf', 'Weighting'], inplace=True)

    return masterdf.reset_index()


def etl_preprocessing(blackrock_date='2019-11-22', vanguard_date='2019-10-31'):
    blackrock_df = blackrock_etl(blackrock_date)
    vanguard_df = vanguard_etl(vanguard_date)

    # Define the columns we want in lists
    blackrock_columns = [
        'Ticker',
        'Name',
        'ISIN',
        'CUSIP',
        'SEDOL',
        'etf',
        'Exchange',
        'Currency',
        'Market Currency',
        'FX Rate',
        'Location',
        'Asset Class',
        'Sector',
        'Weight (%)',
    ]
    vanguard_columns = [
        'symbol',
        'holding',
        'sectorName',
        'countryCode',
        'Weighting',
        'etf'
    ]

    # Cut only the columns needed from the BlackRock and Vanguard dataframes
    blackrock_df = blackrock_df[blackrock_columns]
    vanguard_df = vanguard_df[vanguard_columns]

    # Convert blackrock locations (country column) to 2-letter isocodes
    blackrock_df['Location'] = blackrock_df['Location'].map(country_dict)

    # Clean Vanguard tables
    vanguard_df['holding'] = vanguard_df['holding'].str.upper()
    vanguard_df['symbol'] = vanguard_df['symbol'].str.replace(r'\W', '')

    # If ticker is missing, replace with stock name
    blackrock_df['Ticker'] = np.where(blackrock_df['Ticker'] == '-',
                                      blackrock_df['Name'],
                                      blackrock_df['Ticker']
                                      )
    vanguard_df['symbol'] = np.where(vanguard_df['symbol'] == '-',
                                     vanguard_df['holding'],
                                     vanguard_df['symbol']
                                     )

    # Create a new ticker country column as primary key
    blackrock_df['Ticker Country'] = blackrock_df['Ticker'] + ' ' + blackrock_df['Location']
    vanguard_df['Ticker Country'] = vanguard_df['symbol'] + ' ' + vanguard_df['countryCode']

    return blackrock_df, vanguard_df


def make_class_table():
    '''
    Creates a new classification table
    '''
    blackrock_df, vanguard_df = etl_preprocessing()
    # Merge the datasets together on the tickers named ticker.countryCode
    class_df = pd.merge(blackrock_df, vanguard_df, on='Ticker Country', how='outer')

    # Keep only equities
    class_df = class_df[class_df['Asset Class'] == 'Equity']

    # Check for duplicates and remove
    check_dup_cols = ['Ticker Country', 'Exchange']
    class_df = class_df.drop_duplicates(subset=check_dup_cols)

    # Clean columns
    class_columns = list(blackrock_df.columns) + ['sectorName']
    class_df = class_df[class_columns].rename(columns={'sectorName': 'Sub-Sector'})

    # Sort the data
    class_df.sort_values(['Exchange', 'Ticker'], inplace=True)

    # Save dataframe as csv
    today = datetime.now().date()
    fname = f'ClassificationTable_{today}.csv'
    fpath = os.path.join(data_folder, fname)
    class_df.to_csv(fpath, index=False)
    print(f'Saved {fpath}')


# If this file is run directly, create the classification table
if __name__ == "__main__":
    make_class_table()
