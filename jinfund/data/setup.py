'''
Common data shared across modules
'''
import fnmatch
import os
import pandas as pd
import numpy as np
import yfinance as yf
from pkg_resources import resource_filename


class commonData:
    def __init__(self):
        # Referenced from root
        self.datafolder = resource_filename('data', 'resources')

    def blackrock(self):
        IVV_URL = 'https://www.blackrock.com/au/individual/products/275304/fund/1478358644060.ajax?fileType=csv&fileName=IVV_holdings&dataType=fund'
        IOZ_URL = 'https://www.blackrock.com/au/individual/products/251852/ishares-core-s-and-p-asx-200-etf/1478358644060.ajax?fileType=csv&fileName=IOZ_holdings&dataType=fund'
        IWLD_URL = 'https://www.blackrock.com/au/individual/products/283117/fund/1478358644060.ajax?fileType=csv&fileName=IWLD_holdings&dataType=fund'
        IEMG_URL = 'https://www.blackrock.com/us/individual/products/244050/ishares-core-msci-emerging-markets-etf/1464253357814.ajax?fileType=csv&fileName=IEMG_holdings&dataType=fund'
        self.urls = {
            'IVV': IVV_URL,
            'IOZ': IOZ_URL,
            'IWLD': IWLD_URL,
            'IEMG': IEMG_URL,
        }
        # Blackrock ETFs
        self.etfs = [
            'IVV',
            'IOZ',
            'IWLD',
            'IEMG'
        ]
        return [self.urls, self.etfs]

    def vanguard(self):
        VAS_URL = "https://api.vanguard.com/rs/gre/gra/1.7.0/datasets/auw-retail-holding-details-equity.jsonp?vars=portId:8205,issueType:F"
        VTS_URL = "https://api.vanguard.com/rs/gre/gra/1.7.0/datasets/auw-retail-holding-details-equity.jsonp?vars=portId:0970,issueType:F"
        VEU_URL = "https://api.vanguard.com/rs/gre/gra/1.7.0/datasets/auw-retail-holding-details-equity.jsonp?vars=portId:0991,issueType:F"
        self.urls = {  # Dictionary makes it easy to look up
            'VAS': VAS_URL,
            'VTS': VTS_URL,
            'VEU': VEU_URL
            }
        self.etfs = [  # List of etfs from Vanguard
            'VTS',
            'VAS',
            'VEU'
            ]
        return [self.urls, self.etfs]

    def countrydict(self):
        self.country_map = {  # I had to manually type this out...
            'United States': 'US',
            'Argentina': 'AR',
            'Bermuda': 'BM',
            'Germany': 'DE',
            'Greece': 'GR',
            'China': 'CN',
            'Japan': 'JP',
            'India': 'IN',
            'Australia': 'AU',
            'South Africa': 'ZA',
            'Philippines': 'PH',
            'United Kingdom': 'GB',
            'Korea (South)': 'KR',
            'Indonesia': 'ID',
            'Malaysia': 'MY',
            'Taiwan': 'TW',
            'Hong Kong': 'HK',
            'United Arab Emirates': 'AE',
            'Saudi Arabia': 'SA',
            'Poland': 'PL',
            'Spain': 'ES',
            'Chile': 'CL',
            'Egypt': 'EG',
            'Pakistan': 'PK',
            'Russian Federation': 'RU',
            'France': 'FR',
            'Turkey': 'TR',
            'Qatar': 'QA',
            'Mexico': 'MX',
            'Brazil': 'BR',
            'Canada': 'CA',
            'Hungary': 'HU',
            'Colombia': 'CO',
            'Czech Republic': 'CZ',
            'Norway': 'NO',
            'Peru': 'PE',
            'Switzerland': 'CH',
            'Ireland': 'IE',
            'New Zealand': 'NZ',
            'Italy': 'IT',
            'Austria': 'AT',
            'Singapore': 'SG',
            'Netherlands': 'NL',
            'Denmark': 'DK',
            'Sweden': 'SE',
            'Israel': 'IL',
            'Portugal': 'PT',
            'Belgium': 'BE',
            'Finland': 'FI',
            'Thailand': 'TH'
        }
        return self.country_map


class quickTools:
    def read_class_table():
        # Read the classification file
        for dirpath, dirpaths, fnames in os.walk('.'):
            filtered = fnmatch.filter(fnames, 'Class*csv')
            if filtered:
                class_fname = filtered[0]
                break
        class_df = pd.read_csv(class_fname, index_col=False)

        return class_df


class stockts:
    def __init__(self, ticker):
        '''
        Dependency: Requires yfinance
        Parameters: ticker; must be readable by Yahoo Finance, i.e. have the appropriate exchange suffix
        '''
        self.obj = yf.Ticker(ticker)
        self.info = self.obj.info

    def returns(self):
        self.df = self.obj.history(period='max')
        self.df['Capital Return'] = self.df['Close'] / self.df['Close'].shift(1)
        self.df['Income Return'] = self.df['Dividends'] / self.df['Close'].shift(1)
        self.df['Total Return'] = (self.df['Close'] + self.df['Dividends']) / self.df['Close'].shift(1)

        # Drop first row because it is now useless
        self.df.drop(self.df.index[0], inplace=True)

        # Calculate cumulative returns
        self.df['Cum. Total Return'] = np.cumprod(self.df['Total Return'].values)

        cols_to_return = [
            'Close',
            'Dividends',
            'Capital Return',
            'Income Return',
            'Total Return',
            'Cum. Total Return',
        ]
        return self.df[cols_to_return]
