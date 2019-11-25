'''
Downloads Blackrock ETF holdings data from the Blackrock site
'''
from datetime import datetime
import requests
import os


data_folder = r'raw'

# Helper function
def str2date(asOfDateStr):
    for fmt in ['%d-%b-%Y', '%b %d, %Y']:
        try:
            return datetime.strptime(asOfDateStr, fmt).date()  # ...in a nice format
        except ValueError:
            pass
    
    raise ValueError(f'{asOfDateStr} is not a recognised date/time')
#-----

# Blackrock URLs
IVV_URL = 'https://www.blackrock.com/au/individual/products/275304/fund/1478358644060.ajax?fileType=csv&fileName=IVV_holdings&dataType=fund'
IOZ_URL = 'https://www.blackrock.com/au/individual/products/251852/ishares-core-s-and-p-asx-200-etf/1478358644060.ajax?fileType=csv&fileName=IOZ_holdings&dataType=fund'
IWLD_URL = 'https://www.blackrock.com/au/individual/products/283117/fund/1478358644060.ajax?fileType=csv&fileName=IWLD_holdings&dataType=fund'
IEMG_URL = 'https://www.blackrock.com/us/individual/products/244050/ishares-core-msci-emerging-markets-etf/1464253357814.ajax?fileType=csv&fileName=IEMG_holdings&dataType=fund'

urls = {
    'IVV': IVV_URL,
    'IOZ': IOZ_URL,
    'IWLD': IWLD_URL,
    'IEMG': IEMG_URL,
}

# Blackrock ETFs
etfs = [
    'IVV',
    'IOZ',
    'IWLD',
    'IEMG'
]

# Loop through all ETFs
for etf in etfs:
    response = requests.get(urls[etf])
    if response:
        result = response.content.decode('UTF-8-sig')  # Get rid of the random UTF-8 symbols
        result_splitbyline = result.splitlines()  # Split the long-ass string into a list of rows
        asOfDate = result_splitbyline[2].split('of,')[1][1:-1]  # Get the holding date in Row 3...
        asOfDate = str2date(asOfDate)
        
        filename = f'{etf}_{asOfDate}.csv'
        filepath = os.path.join(data_folder, filename)
        open(filepath, 'w', encoding='utf-8').write(result)  # Then save it
        print(f'Saved {filename} in {filepath}')
        
    else:
        print('The URL is broken! Check the URL to the holdings csv is correct')
print('All files loaded!\n')