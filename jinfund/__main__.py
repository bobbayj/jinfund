# Standard library imports


# Local imports
from analysis import lookthru
from data import etl, download

# Get the data frames
blackrock_df, vanguard_df = etl.etl_preprocessing()

# Update data
download.blackrock()
download.vanguard()

# Pass the weights through after instantiating lookthru
lookthru = lookthru.analysis(blackrock_df, vanguard_df)
blackrock_df, vanguard_df = lookthru.pass_weights()
