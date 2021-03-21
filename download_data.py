import pandas as pd
import numpy as np
import pandas_datareader.data as web
import datetime
import calendar

schiller_data = 'data/shiller_sp500_final.csv'

def download_data():

    #1 -- GET DIVIDEND PAYMENTS FROM SCHILLER --
    dateparse = lambda x: datetime.datetime.strptime(str(x), '%Y.%m')
    
    sp500 = pd.read_csv(schiller_data, parse_dates = ['Date'], date_parser=dateparse)
    
    #A) Original csv has format YYYY.MM ie 2019.01 for 2019 January. However, October is 2019.1 instead of 2019.10 which...
    #... I fix below since the datetime parser would treat it as January otherwise.
    #B) We also shift the data to the end of month.    
    for i in range(0, len(sp500)):
    
        #A)Shift days to end of month
        d = sp500.iloc[i][0]
        sp500.Date[i] = datetime.date(d.year, d.month, calendar.monthrange(d.year, d.month)[-1])
        
        #B)Fix October bug from Excel file
        if (str(sp500.iloc[i][0])[6] == str(9)) and (i + 1 < len(sp500)):
            sp500.Date[i+1]= sp500.Date[i+1].replace(month=10)

    #Convert to right datatype.
    sp500['Date'] = pd.to_datetime(sp500['Date'])
    
    #2 --GET DAILY PRICE DATA FROM YAHOO -- 
    #Note, the library uses Unix time which starts from 1970 so cannot get earlier dates 
    start_date = start_date = '1970-01-01'
    end_date = datetime.datetime.today().strftime("%Y-%m-%d")
    
    daily_sp500 = web.DataReader('^GSPC', 'yahoo', start=start_date, end=end_date).reset_index()
    daily_sp500 = daily_sp500.rename(columns={"Adj Close": "Price"})
    
    data = pd.merge(daily_sp500[['Date','Price']].assign(grouper=daily_sp500['Date'].dt.to_period('M')),
               sp500[['Dividend','CPI','Long_Interest_Rate_GS10', 'CAPE']].assign(grouper=sp500['Date'].dt.to_period('M')),
               how='left', on='grouper')
               
    return data