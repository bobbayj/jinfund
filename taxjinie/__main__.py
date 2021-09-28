from transactions import tx_loader
from analysis import tax, performance

def main():
    commsec = tx_loader.Loader()
    commsec.build()

    # tax_reporting = tax.Tax(2021)
    # tax_reporting.capital_gain_events()
    # tax_reporting.upcoming_cgtdiscounts()
    # tax_reporting.cgt_report(output_type='excel')
    # tax_reporting.export_tx_history()

    performance_reporting = performance.Performance()
    performance_reporting.monthly_cashflows(export=True)

if __name__ == '__main__':
    main()