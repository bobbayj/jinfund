from taxjinie.transactions import tx_loader
from taxjinie.analysis import portfolio, tax

def main():
    commsec = tx_loader.Loader()
    commsec.build()

    reporting = tax.Tax(2021)
    reporting.capital_gain_events()
    reporting.cgt_report(output_type='excel')

if __name__ == '__main__':
    main()