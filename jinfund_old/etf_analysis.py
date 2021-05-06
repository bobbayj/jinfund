# Standard library imports
# Local imports
from analysis import bystock
from data import etl, download

# Update data
download.blackrock()
download.vanguard()

# Get the data frames
blackrock_df, vanguard_df = etl.etl_preprocessing()


# Pass the weights through after instantiating lookthru
lookthru = bystock.analysis(blackrock_df, vanguard_df)
blackrock_df, vanguard_df = lookthru.pass_weights()
