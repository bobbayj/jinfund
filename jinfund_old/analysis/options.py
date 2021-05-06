# Standard
import numpy as np
import datetime
from scipy.stats import norm

# 3rd party
import yfinance as yf
import holidays

# Local
import datehandler

class Options:
    def __init(self):
        pass

    @classmethod
    def historical_vol(cls, ticker=None,period='3mo'):
        '''Calcualtes historical volatility
        
        Arguments:
            period {str} -- Valid periods: '3mo', '1y'
        
        Keyword Arguments:
            ticker {str} -- Underlying ticker to check in yahoo finance format (default: {None})
        '''        
        if period == '1y':
            days = 252
        elif period == '3mo':
            days = 63
        else:
            raise Exception('Invalid period')
        
        prices = yf.Ticker(ticker).history(period=period)

        prices['Close_prev'] = prices['Close'].shift()
        prices['ccReturns'] = np.log(prices.Close/prices.Close_prev)
        std_dev = np.std(prices.ccReturns)
        hvol = std_dev/np.sqrt(days/252)  # 252 trading days in a year on average

        return hvol
        
    @classmethod
    def bsm_call(cls, ticker, expiry, strike, rf=0.0225):
        '''Calculates option price using the black-scholes model
        
        Arguments:
            ticker {str} -- Underlying ticker in yahoo finance format
            expiry {str} -- Option expiry date
            strike {float} -- Strike price
        
        Keyword Arguments:
            rf {float} -- Short-term risk-free rate (default: {0.0225})

        Returns:
            val {float} -- Option valuation from BSM
        '''

        # Compute variables
        s0 = yf.Ticker(ticker).history(period='1d').Close.sum()
        vol = cls.historical_vol(ticker)
        print(s0, vol)

        expiry = datehandler.to_iso(expiry).date()
        start = datetime.datetime.today().date()
        if start.weekday() in [5,6]:
            start = start - datetime.timedelta(days=start.weekday()) + datetime.timedelta(days=4)
        nsw_holidays = holidays.AU(prov='NSW')
        years = np.busday_count(start, expiry, holidays=nsw_holidays[start:expiry])/252
        print(years)

        d1 = (np.log(s0/strike) + years*(rf + (vol**2)/2)) / (vol * np.sqrt(years))
        d2 = d1 - (vol * np.sqrt(years))

        n1 = norm.cdf(d1)
        n2 = norm.cdf(d2)
        print((np.log(s0/strike) + years*(rf + (vol**2)/2)))
        print(f'd1 = {d1} | d2 = {d2}')
        print(f'n1 = {n1} | n2 = {n2}')

        # Compute value of call option
        val = s0*n1 - strike*np.exp(-rf*years)*n2

        return val