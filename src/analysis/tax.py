from pathlib import Path
import pandas as pd
import numpy as np

# Local imports
from . import portfolio

class Tax():
    def __init__(self) -> None:
        self.portfolio = portfolio.build()
        self.cgt_log = []
        self.all_cg_events = pd.DataFrame()
    
    def capital_gain_events(self):

        for ticker in self.portfolio['Ticker'].unique():
            ticker_capital_gain_events = self.ticker_cg(ticker)
            if len(ticker_capital_gain_events) > 0:
                self.all_cg_events = pd.concat([self.all_cg_events,ticker_capital_gain_events])

    def ticker_cg(self, ticker):
        '''Calculates capital gains using Last in, first out logic
        '''
        tx_df = self.portfolio[self.portfolio['Ticker'] == ticker]
        dates = list(tx_df.index)

        txs = tx_df.to_dict('list')     # For easier sequential access to each row
        buy_queue = []                  # Flush for new ticker
        cgt_events=  []                 # Flush for new ticker

        for i, date in enumerate(dates):
            tx_dict = {
                'Ticker': ticker,
                'Date': date,
                'Volume': txs['Volume'][i],
                'Price': txs['Price'][i],
                'PriceIncBrokerage': txs['PriceIncBrokerage'][i],
                'Brokerage': txs['Brokerage'][i],
            }
            tx_vol = tx_dict['Volume']  # Simpler to read
            tx_cg, tx_cg_taxable = 0, 0  # Reset to 0 for each new tx

            print(tx_dict)

            if tx_vol > 0:  # Buys in queue
                buy_queue.append(tx_dict)
            else:  # Sells reduced by
                buy_logs = []                                       # Flush buy logs
                while tx_vol != 0:                                  # Loop until all the sold volume is accounted for
                    if buy_queue[-1]['Volume'] == 0:                # Catch any 0 volume buy parcels
                        buy_parcel = buy_queue.pop()
                        continue
                    elif abs(tx_vol) < buy_queue[-1]['Volume']:     # Sell volume is less than or equal to previous buy volume
                        cg, cg_taxable = self.__cg_calc(buy_queue[-1], tx_dict, limiter='sell')
                        buy_log = buy_queue[-1].copy()              # For logging - initial shares in buy_parcel
                        buy_queue[-1]['Volume'] += tx_vol           # Reduce LIFO buy_volume by sale_volume (sale_volume is negative)
                        tx_vol = 0
                    else:                                           # Sell volume greater than previous buy volume
                        buy_parcel = buy_queue.pop()                # Remove buy_parcel from buy_queue as it has been depleted
                        cg, cg_taxable = self.__cg_calc(buy_parcel, tx_dict, limiter='buy')
                        buy_log = buy_parcel.copy()                 # For logging - remaining shares in buy_parcel
                        tx_vol += buy_parcel['Volume']              # Increase sale_volume by LIFO buy_volume (sale_volume is negative)
                    tx_cg += cg
                    tx_cg_taxable += cg_taxable
                    buy_logs.append(buy_log)                        # Keep log of buys associated with sale

                cgt_detailed_log = { # Log event for reporting
                    'ticker': ticker,
                    'date': date,
                    'volume': txs['Volume'][i],
                    'cg': tx_cg,
                    'cgt': tx_cg_taxable,
                    'buy_parcels': buy_logs,
                    'sell_parcel': tx_dict,
                }
                self.cgt_log.append(cgt_detailed_log)

                cgt_event = {  # Dict to store capital gain event
                    'Ticker': ticker,
                    'Date': date,
                    'CapitalGains': tx_cg,
                    'CapitalGainsTaxable': tx_cg_taxable,
                    }
                cgt_events.append(cgt_event)
        return pd.DataFrame(cgt_events)
    
    def __cg_calc(self, buy_parcel, sell_parcel, limiter='buy'):  # Aux function
        '''Calculates capital gains given buy and sell parcels, using the the buy or sell volume. Considers brokerage as tax deductible
        
        Arguments:
            buy_parcel {dict} -- Requires keys: [Date, Volume, TradePrice, Brokerage]
            sell_parcel {dict} -- Requires keys: [Date, Volume, TradePrice, Brokerage]
            limiter {string} -- ['buy','sell']; Defines the buy or sell volume as the limiting volume for the calculation
        Returns:
            float -- calculated capital gains
        '''
        limiter_options = ['buy','sell']
        if limiter not in limiter_options:
            raise ValueError(f'Invalid partial type. Expected one of: {limiter_options}')
        if limiter == 'buy':  # More buy volume than sell volume
            volume = buy_parcel['Volume']
        else:  # More sell volume than buy volume
            volume = abs(sell_parcel['Volume'])

        buy_value = volume * buy_parcel['PriceIncBrokerage']  # PriceIncBrokerage incldues brokerage
        sell_value = volume * sell_parcel['PriceIncBrokerage']  # PriceIncBrokerage incldues brokerage

        cg = sell_value - buy_value
        if ((sell_parcel['Date'] - buy_parcel['Date']).days > 365) and (cg > 0):
            cg_taxable = cg / 2 # Apply any capital gains discounts if applicable
        else:
            cg_taxable = cg
        
        return cg, cg_taxable