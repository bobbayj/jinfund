# jin-fund

Jin-fund is a basic Python package to help you analyse your equity portfolio and quickly process basic admin tasks.

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

Note: **Currently under-development**. However, you can play around using Jupyter Notebooks (see [Basic Usage in Jupyter Notebooks](#Basic-Usage-in-Jupyter-Notebooks))

Run `app.exe` to open the GUI.

- You will need to import the broker trade data to this tool, and select which broker this is
  - The file will be copied to `jinfund/data` and renamed to `{broker_name}.csv`. E.g. Transactions exported from commsec will be renamed `commsec.csv`
  - If your broker is not in the drop-down list, contact and provide me a sample csv file so I can support the broker
- You will also need manually update the dividends
  - Click "Update Dividends" to open `div.csv` and make edits
  - Remember to save and close the file before using this tool any further
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
