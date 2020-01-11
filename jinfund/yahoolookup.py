import yfinance as yf

class Stock:  
    '''Wrapper for yfinance to look up stock details.
    Creates relevant yahoo ticker from input

    Arguments:
        ticker {string} -- 3-letter ticker
        market {string} -- market to be mapped to Yahoo
    '''    
    def __init__(self,ticker,market):
        yticker = f'{ticker}.{self.market_mapper(market)}'
        self.stock = yf.Ticker(yticker)

    @staticmethod
    def market_mapper(market_code):
        market_mapping = {
            'ASX': 'AX',
        }
        return market_mapping[market_code]

    def actions(self):
        return self.stock.actions

    def dividends(self):
        return self.stock.dividends

    def splits(self):
        return self.stock.splits
