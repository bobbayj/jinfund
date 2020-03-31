# Standard imports
import pandas as pd
from datetime import datetime

# Local imports
from portfolio.commsec import Trades

class AutoCGT:
    def __init__(self):
        t = Trades()
        self.trade_df = t.all

        self.df = self.build_from_trades()
    

    def build_from_trades(self):    
        '''Constructs capital gains for all trades
        
        Returns:
            DataFrame -- of capital gains for all tickers. MultiIndex: (Date, Ticker), Column: [CapitalGain]
        '''        
        tickers = list(sorted(set(self.trade_df.reset_index().Ticker.to_list())))
        capital_gains = pd.DataFrame()  # Initalise empty df

        for ticker in tickers:
            tick_cg_df = self.ticker_cgt_events(ticker)
            if len(tick_cg_df) > 0:
                if len(capital_gains) == 0:
                    capital_gains = tick_cg_df
                else:
                    capital_gains = pd.concat([capital_gains,tick_cg_df])

        capital_gains = capital_gains.set_index('Date').sort_index()

        return capital_gains

    def ticker_cgt_events(self, ticker):
        '''Analyses CGT events based off LIFO logic
        
        Arguments:
            ticker {string} -- Stock ticker to analyse. Must be in transaction history
        
        Returns:
            DataFrame -- Columns: [Ticker, Date, CapitalGain]
        '''                
        # LIFO tax logic...tends to minimise tax on average due to lower CG
        # LIFO = last-in, first-out. Most recently purchased  volume is the first to be sold
        

        ticker_df = self.trade_df.xs(ticker,level=1,axis=0)
        dates = list(ticker_df.index)
        txs = ticker_df.to_dict('list')
        buy_queue = []
        cgt_events=  []

        for i, date in enumerate(dates):
            tx_dict = {
                'Date': date,
                'Volume': txs['Volume'][i],
                'TradePrice': txs['TradePrice'][i],
                'EffectivePrice': txs['EffectivePrice'][i],
                'Brokerage': txs['Brokerage'][i],
            }
            tx_vol = tx_dict['Volume']
            tx_cg, tx_cg_taxable = 0, 0

            if tx_vol > 0:  # Buys in queue
                buy_queue.append(tx_dict)
            else:  # Sells reduced by 
                while tx_vol != 0:                                  # Loop until all the sold volume is accounted for
                    if tx_vol <= buy_queue[-1]['Volume']:           # Sell volume is less than or equal to previous buy volume
                        cg, cg_taxable = self.cg_calc(buy_queue[-1], tx_dict, partial='sell')
                        tx_cg += cg
                        tx_cg_taxable += cg_taxable
                        buy_queue[-1]['Volume'] += tx_vol           # Reduce LIFO buy_volume by sale_volume (sale_volume is negative)
                        tx_vol = 0
                    else:                                           # Sell volume greater than previous buy volume
                        buy_parcel = buy_queue.pop()                # Remove buy_parcel from buy_queue as it has been depleted
                        cg, cg_taxable = self.cg_calc(buy_parcel, tx_dict, partial='buy')       
                        tx_cg += cg
                        tx_cg_taxable += cg_taxable
                        tx_vol += buy_parcel['Volume']              # Increase sale_volume by LIFO buy_volume (sale_volume is negative)

                cgt_event = {  # Dict to store capital gain event
                    'Ticker': ticker,
                    'Date': date,
                    'CapitalGains': tx_cg,
                    'CapitalGainsTaxable': tx_cg_taxable,
                    }
                cgt_events.append(cgt_event)
        return pd.DataFrame(cgt_events)
    
    def cg_calc(self, buy_parcel, sell_parcel, partial=['buy','sell']):  # Aux function
        '''Calculates capital gains given buy and sell parcels, using the the buy or sell volume
        
        Arguments:
            buy_parcel {dict} -- Requires keys: [Date, Volume, TradePrice, Brokerage]
            sell_parcel {dict} -- Requires keys: [Date, Volume, TradePrice, Brokerage]
            partial {string} -- ['buy','sell']; Defines whether to use the buy or sell volume for the calculation
        Returns:
            float -- calculated capital gains
        '''        
        if partial == 'sell':
            volume = abs(sell_parcel['Volume'])
        elif partial == 'buy':
            volume = buy_parcel['Volume']

        buy_value = volume * buy_parcel['TradePrice']
        sell_value = volume * sell_parcel['TradePrice']

        cg = sell_value - buy_value
        if ((sell_parcel['Date'] - buy_parcel['Date']).days > 365) and (cg > 0):
            cg_taxable = cg / 2 # Apply any capital gains discounts if applicable
        else:
            cg_taxable = cg
        cg_taxable -= (buy_parcel['Brokerage'] + sell_parcel['Brokerage')  # Brokerage is tax deductible
        return cg, cg_taxable

    def fy(self, yr_end = None, summary = True):
        '''Returns view of capital gains for the given financial year.
        
        Keyword Arguments:
            yr_end {Integer} -- Must be full year, e.g. 2020. Defaults to current FY (default: {None})
            summary {bool} -- Summarises capital gains per ticker. Set to False for date details (default: {True})
        
        Returns:
            DataFrame -- View of capital gains
        '''        
        if yr_end is None:
            today = datetime.today()
            yr_end = today.year
            if today.month > 6:
                yr_end += 1
        
        yr_start = yr_end-1
        fy_df = self.df.loc[f'{yr_start}-07-01':f'{yr_end}-06-30']

        if summary:
            fy_df = fy_df.groupby('Ticker').sum()
        
        print(f'''
Capital gains for \tFY{yr_start}-{yr_end}
Total CG:\t\t ${fy_df['CapitalGains'].sum(): .2f}
Total CGTaxable:\t ${fy_df['CapitalGainsTaxable'].sum(): .2f}
(Uses LIFO method)
        ''')

        return fy_df
        