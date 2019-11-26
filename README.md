# jin-fund
Robo-advice for ETF Investing. Measuring the exposure of your ETF investments by:
1. Geography
2. Sector

## How to use
1. Run `__main__.py`
2. The `data` package:
    - `download`; downloads raw data for Blackrock and Vanguard ETFs
    - `etl`; additional methods to help pre-process that raw data
3. The `analysis` package:
    - `bystock`; module contains portfolio analysis at the stock level and yahoo Finance links

## Data Sources
- Blackrock ETFs; .csv files updated daily
- Vanguard ETFs; .json requests updated monthly
- Yahoo calls; yfinance library updated daily