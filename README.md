# jin-fund

Jin-fund is a basic Python package to help you analyse your equity portfolio and quickly process basic admin tasks.

It is designed to automate as much of the portfolio administration away as possible, allowing you to focus on what you do best - invest!

## Basic Usage

1. Run `app.py`
2. Use the portfolio tool

### Limitations

- Price data not currently stored in a database; streamed direct from Yahoo Finance
  - If the stock is not in Yahoo Finance, it will not be available at all
- Due to data limitations, dividends (cash or scrip) are not captured and must be manually entered

## Future: Robo-investing

Ideally, this evolves into a robo-advice tool. Currently, it can measuring the exposure of ETF investments by:

1. Geography
2. Sector

However, this is a long way off and will require:

1. Developing investment strategies
2. Partnering with an AFSL holder!

### Current functionality

Currently, the package can data scrape ETF holdings and load them into a dataframe.

1. Run `__main__.py`
2. The `data` package:
    - `download`; downloads raw data for Blackrock and Vanguard ETFs
    - `etl`; additional methods to help pre-process that raw data
3. The `analysis` package:
    - `bystock`; module contains portfolio analysis at the stock level and yahoo Finance links

### Data Sources

- Blackrock ETFs; .csv files updated daily
- Vanguard ETFs; .json requests updated monthly
- Yahoo calls; yfinance library updated daily