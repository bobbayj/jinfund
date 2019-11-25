'''
Downloads Vanguard ETF holdings data from the Vanguard site
'''
import requests
import json
import pandas as pd
import os
import setup

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
print('All ETF holdings updated!')
