# System imports
import pandas as pd
from datetime import datetime, timedelta
from dateutil.parser import parse

def to_iso(date):
    if type(date) is not datetime.date:
        date = pd.to_datetime(date, dayfirst=True)
    return date

def date_list(start_date, end_date, only_weekdays=True, ascending=False):
    '''Create a datetime list of all dates between two given periods in descending order
    
    Keyword Arguments:
        start_date {datetime.date} -- Start date
        end_date {datetime.date} -- End date
        only_weekdays {bool} -- Set if you want to have weekdays only, or include weekends (default: {True})
        ascending {bool} -- Change order of dates returned (default: {False})
    
    Returns:
        list -- list of datetime.date values
    '''
    print()
    delta = end_date - start_date

    dates = []

    for i in range(delta.days + 1):
        date = start_date + timedelta(days = i)

        if only_weekdays:
            if date.weekday() in range(5):
                dates.append(date)

    if not ascending:
        dates = sorted(dates,reverse=True)

    return dates