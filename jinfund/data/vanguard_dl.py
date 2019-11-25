'''
Downloads Vanguard ETF holdings data from the Vanguard site
'''
import requests
import json
import pandas as pd
import os

data_folder = r'raw'

# Most important is to get the right portfolio ID from Vanguard
# Can get this by inspecting elements in the webpage
# (Go to Network tab and reload to see .json requests sent)
VAS_URL = "https://api.vanguard.com/rs/gre/gra/1.7.0/datasets/auw-retail-holding-details-equity.jsonp?vars=portId:8205,issueType:F"
VTS_URL = "https://api.vanguard.com/rs/gre/gra/1.7.0/datasets/auw-retail-holding-details-equity.jsonp?vars=portId:0970,issueType:F"
VEU_URL = "https://api.vanguard.com/rs/gre/gra/1.7.0/datasets/auw-retail-holding-details-equity.jsonp?vars=portId:0991,issueType:F"

urls = {  # Dictionary makes it easy to look up
    'VAS': VAS_URL,
    'VTS': VTS_URL,
    'VEU': VEU_URL
       }
etfs = [  # List of etfs from Vanguard
    'VTS',
    'VAS',
    'VEU'
    ]

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
