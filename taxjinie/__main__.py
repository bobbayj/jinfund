from taxjinie.transactions import tx_loader
from taxjinie.analysis import tax

def main():
    commsec = tx_loader.Loader()
    commsec.build()

    reporting = tax.Tax(2021)
    reporting.capital_gain_events()
    reporting.upcoming_cgtdiscounts()
    reporting.cgt_report(output_type='excel')
    reporting.export_portfolio()

if __name__ == '__main__':
    main()