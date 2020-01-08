'''
Reads and prepares Commsec transaction.csv files
'''

# Structure as Class object

# init
    # Read csv. Note that transactions only show on the T+2 date

    # Split details by space
        # If details[0] not in ['B','S'], skip delete row

    # Create dataframe
        # Index = Date
        # Columns = type | asxCode | volume | debit | credit | orderPrice
    # Update price to include brokerage
        # price = debit or credit / volume
        # Add price as column
        # combine debit and credit cols as a single col: value
        # Add brokerBps as column: int(abs(price/orderPrice-1)*100), remove orderPrice col
    
# Methods (rtn functions)
    # final dataframe
    # buys only
    # sells only
    # total brokerage cost (skip)

# -------
# Testing script
# if __name__ == __main__: