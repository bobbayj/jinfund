'''
Downloads Blackrock ETF holdings data from the Blackrock site
'''
from datetime import datetime
import requests
import os
from . import setup


# Helper function
def str2date(asOfDateStr):
    for fmt in ['%d-%b-%Y', '%b %d, %Y']:
        try:
            # ...in a nice format
            return datetime.strptime(asOfDateStr, fmt).date()
        except ValueError:
            pass

    raise ValueError(f'{asOfDateStr} is not a recognised date/time')


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
print('All files loaded!\n')
