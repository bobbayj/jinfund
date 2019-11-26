'''
Lookthru function that passes weightings at ETF level through to stock level
'''
import numpy as np


class analysis():
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
