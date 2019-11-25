import pandas as pd
import os
import csv
import setup

# Get variables from setup module
[urls, etfs] = setup.commonData().vanguard()
data_folder = setup.commonData().datafolder

# Get filenames of blackrock etf's
csvfiles = []
for dirname, dirnames, filenames in os.walk(data_folder):
    for filename in filenames:
        fpath = os.path.join(dirname, filename)

        for etf in etfs:
            if etf in fpath:
                csvfiles.append(fpath)

# Get dates
dates = list(set([filename.split('_')[1].split('.')[0]
             for filename in csvfiles]))

# Define columns needed
cols_needed = [
    'Date',
    'etf',
    'Ticker',
    'Weighting',
    ]

# Initiatve variables
masterdf = pd.DataFrame()

# Read csv's as dataframes and aggregate into a master
for file in csvfiles:
    if dates[-1] in file:  # Latest date only
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
        df.insert(0, 'Date', dates[-1])

        # Add etf symbol
        etf = file.split('_')[0]
        df.insert(1, 'etf', etf)

        # Only keep columns we need
        df = df[cols_needed]

        # Append dataframe to master
        masterdf = masterdf.append(df, ignore_index=True)

# Intermediate aggregated dataframe...
# symbols have not seen a final check with classification table
# masterdf.sort_values(['etf', 'Weighting'], inplace=True)  # Test
