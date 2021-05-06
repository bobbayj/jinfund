'''
Lookthru function that passes weightings at ETF level through to stock level
'''
import numpy as np
import yfinance as yf


class portfolio:
    def __init__(self, blackrock_df, vanguard_df):
        self.blackrock_df = blackrock_df
        self.vanguard_df = vanguard_df

        # Ensure dates for ETF files are valid - holdings must exist!
        self.etf_dates = {
            'blackrock': '2019-11-14',
            'vanguard': '2019-10-31',
        }

        # Setup strategic allocations for ETFs
        self.etf_weights = {
            'VAS': 0.5,
            'VEU': 0,
            'VTS': 0,
            'IEMG': 0,
            'IOZ': 0.5,
            'IVV': 0,
            'IWLD': 0,
        }

        # Raise error if the weightings do not sum to 1
        if sum(self.etf_weights.values()) != 1:
            raise ValueError('Total weighting must equal to 1!')
        else:
            print('SSA Weights are valid and equal to 1')

    def pass_weights(self):
        # lookthru weightings to the stock level for each ETF
        for etf, weight in self.etf_weights.items():
            self.blackrock_df['Weight (%)'] = np.where(
                self.blackrock_df['etf'] == etf,
                self.blackrock_df['Weight (%)']*weight,
                self.blackrock_df['Weight (%)']
                )
            self.vanguard_df['Weighting'] = np.where(
                self.vanguard_df['etf'] == etf,
                self.vanguard_df['Weighting']*weight,
                self.vanguard_df['Weighting']
                )
        return self.blackrock_df, self.vanguard_df


class yah:
    '''
    Dependency: Requires yfinance
    Parameters: ticker; must be readable by Yahoo Finance, i.e. have the appropriate exchange suffix
    '''
    def __init__(self, ticker):
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