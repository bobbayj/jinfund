# Standard imoports
from datetime import datetime
import requests
import os
import json
import pandas as pd

# Local imports
from . import setup


# Helper function
def str2date(asOfDateStr):
    '''
    Downloads Blackrock ETF holdings data from the Blackrock site
    '''
    for fmt in ['%d-%b-%Y', '%b %d, %Y']:
        try:
            # ...in a nice format
            return datetime.strptime(asOfDateStr, fmt).date()
        except ValueError:
            pass

    raise ValueError(f'{asOfDateStr} is not a recognised date/time')


def blackrock():
    # Get variables from setup module
    [urls, etfs] = setup.commonData().blackrock()
    data_folder = setup.commonData().datafolder

    # Loop through all ETFs
    for etf in etfs:
        response = requests.get(urls[etf])
        if response:
            # Get rid of the random UTF-8 symbols
            result = response.content.decode('UTF-8-sig')
            # Split the long-ass string into a list of rows
            result_splitbyline = result.splitlines()
            # Get the holding date in Row 3...
            asOfDate = result_splitbyline[2].split('of,')[1][1:-1]
            asOfDate = str2date(asOfDate)

            filename = f'{etf}_{asOfDate}.csv'
            filepath = os.path.join(data_folder, filename)
            open(filepath, 'w', encoding='utf-8').write(result)  # Then save it
            print(f'Saved {filename} in {filepath}')

        else:
            print('The URL is broken!\n',
                  'Check the URL to the holdings csv is correct')
    print('All Blackrock ETF holdings updated..\n')


def vanguard():
    '''
    Downloads Vanguard ETF holdings data from the Vanguard site
    '''
    # Get variables from setup module
    [urls, etfs] = setup.commonData().vanguard()
    data_folder = setup.commonData().datafolder

    # Download all the portfolio data for given ETFs
    for etf in etfs:
        response = requests.get(urls[etf])

        if response:
            result = response.text

            # remove the "callback([" string and extra "])" at end
            data = json.loads(result[10:len(result)-2])
            df = pd.DataFrame(data['sectorWeightStock'])
            df.insert(0, 'Date', data["asOfDate"].split("T")[0])
        else:
            print(f'Failed to get data for {etf}! Skipping...')
            pass
        # forward-fill country codes for all AU stocks
        if etf == 'VAS':
            df.fillna('AU', inplace=True)
        filename = f'{etf}_{data["asOfDate"].split("T")[0]}.csv'
        fpath = os.path.join(data_folder, filename)
        df.to_csv(fpath, index=False)
        print(f'Saved "{filename}" in {fpath}')
    print('All Vanguard ETF holdings updated..\n')
