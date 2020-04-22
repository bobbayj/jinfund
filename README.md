# TaxJinie (part of the jinfund :) )

TaxJinie is a basic tool to help you analyse your equity portfolio and quickly process basic admin tasks. (Also available as an .exe on Dropbox)[https://www.dropbox.com/sh/s5maw2wh1kczvcr/AACV7-41mPaV-gGfKP6BoaRDa?dl=0]

It is designed to automate as much of the portfolio administration away as possible, allowing you to focus on what you do best - invest!
**Currently only calculates your tax returns from your trade and dividend history**

## Getting Started

### Prequisites

- You need to download your broker transaction history as a `.csv`
  - This is safer than providing your broker login details to automate this!
  - **Currently only supports Commsec transactions**
    - Please provide me a `.csv` sample from other brokers so that I can support them
- You also need to manually enter dividends (cash or scrip from dividend reinvestment plans) into a `.csv`
  - See sample file at `jinfund/data/samples/divs.csv` for required layout
  - Unfortunately, I am unable to automate this without access to the share registrars and your personal holdings
  - On the bright side, share registrars provide ample information for you to quickly fill-out dividends received

### Quick Start using GUI

- Run `TaxJinie.exe` (if you want to test this out) or `cli.py` (if you're familiar how to do so with python)
  - The `.exe` can be downloaded from (Dropbox)[[https://www.dropbox.com/sh/s5maw2wh1kczvcr/AACV7-41mPaV-gGfKP6BoaRDa?dl=0]]. It has been compiled from this repo only so is safe!
  - If going the python route, make sure you run `pipenv install` to install the few dependencies needed
- You will need to import the broker trade data to this tool, and select which broker this is
  - The file will be copied to `jinfund/data` and renamed to `{broker_name}.csv`. E.g. Transactions exported from commsec will be renamed `commsec.csv`
  - If your broker is not in the drop-down list, contact and provide me a sample csv file so I can support the broker
- You will also need manually update the dividends
  - Dividends need to be in a specific order
  - See `data/samples/div.csv` for the required structure. **Franking details are optional**
- Click `Generate CGT Report` to generate a `.csv` summary of the capital gains and capital gains taxable
- Click `Export CGT Details` to generate a detailed `.csv` report of all capital gains events and their associated transactions
- Click `Change Output Path` to change the output destination.
  - Currently defaults to `jinfund/outputs`

### Basic Usage in Jupyter Notebooks

*You may want to run `pipenv install` in the terminal to install dependencies first.*

If you are capable, feel free to experiment in a Jupyter Notebook. Here is some documentation of the main modules in use.

#### tax.AutoTax

> Automatically calculates capital gains tax over a specified period for one or all stocks using trade and scrip dividend data.

| Attributes | Description |
| --- | --- |
| `.finyear` | Sets the financial year for analysis. *Defaults to current financial year* |
| `.cgt_log.view`| View the capital gains tax log (dict-like) |
| `.df` | pd.DataFrame of capital gains for all trades |

| Methods | Description |
| --- | --- |
| `.fy_view(yr_end = None, summary = True)` | Provides a `pd.DataFrame()` snapshot of capital gains for period. <br> *Defaults to current FY* |
| `.cgt_report(to_csv:bool=True)` | Creates a .csv report of all capital gains events for the given year and the parcels involved. <br>*`to_csv=False` does not export a `.csv`* |
| `.cgt_details(self, ticker:str=None,`<br>`show_all:bool=True, to_csv:bool=True)`| Creates a .csv report for all associated buy and sell transactions of each capital gains event.|

#### transactions.Transactions

> Combines trades from brokers and manually-inputted dividends into one pd.DataFrame. Currently only supports Commsec trades

| Attributes | Description |
| --- | --- |
| `.cash_dividends` | Returns a pd.DataFrame of cash dividends |
| `.tx_df` | Combined pd.DataFrame of all broker trade data and manually-inputted dividends |
| `.t_df` | pd.DataFrame of all broker trade data |
| `.d_df` | pd.DataFrame of manually-inputted dividends |

### Limitations

- Price data not currently stored in a database; streamed direct from Yahoo Finance
  - If the stock is not in Yahoo Finance, it will not be available at all
- Due to data limitations, dividends (cash or scrip) are not captured and must be manually entered

---

Note: *Everything below this line is blue-sky stuff, so don't worry about it too much*

## Future: Robo-investing

Ideally, this evolves into a robo-advice tool. Currently, it can measuring the exposure of ETF investments by:

1. Geography
2. Sector

However, this is a long way off and will require:

1. Developing investment strategies
2. Partnering with an AFSL holder!

### Current functionality

Currently, the package can data scrape ETF holdings and load them into a dataframe.

1. The `data` package:
    - `download`; downloads raw data for Blackrock and Vanguard ETFs
    - `etl`; additional methods to help pre-process that raw data
2. The `analysis` package:
    - `bystock`; module contains portfolio analysis at the stock level and yahoo Finance links

### Data Sources

- Blackrock ETFs; .csv files updated daily
- Vanguard ETFs; .json requests updated monthly
- Yahoo calls; yfinance library updated daily
