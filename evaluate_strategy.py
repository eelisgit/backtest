import pandas as pd
import numpy as np
import pandas_datareader.data as web
import datetime
import calendar
import seaborn as sns
import matplotlib.pyplot as plt
import matplotlib.ticker as tkr
from tqdm import tqdm
from process_data import Data_Handler
from copy import deepcopy
from strategies import Strategies
from process_data import Data_Handler
from download_data import download_data

def make_plots(d, starting_amount = 100_000):

    #PLOT 1
    ending_value_fi = d.df.tail(1)['fi_Value'].iloc[0]
    ending_value_fi_nr = d.df.tail(1)['fi_no_reinvest_Value'].iloc[0]
    ending_value_shbl = d.df.tail(1)['shbl_Value'].iloc[0]
    ending_price = d.df.tail(1)['Real_Price'].iloc[0]
    starting_price = d.df.head(1)['Real_Price'].iloc[0]

    ending_date = d.df.tail(1)['Date'].iloc[0]
    starting_date = d.df.head(1)['Date'].iloc[0]
    
    year_diff = (ending_date - starting_date) / datetime.timedelta(days=365)
    
    annualized_return_fi = (ending_value_fi / starting_amount) **(1/year_diff) - 1
    annualized_return_fi_nr = (ending_value_fi_nr / starting_amount) **(1/year_diff) - 1
    annualized_return_shbl = (ending_value_shbl / starting_amount) **(1/year_diff) - 1
    annualized_price = (ending_price / starting_price) **(1/year_diff) - 1
    
    fig, ax = plt.subplots(figsize=(12,8))
    lns1 = ax.plot(d.df.Date,d.df.fi_Value, 'b', label = "Fully invested strategy annual return: {:.2%}"\
                                                .format(annualized_return_fi))
    lns2 = ax.plot(d.df.Date,d.df.shbl_Value, 'r', label = "Sell high/buy low strategy annual return: {:.2%}"\
                                                .format(annualized_return_shbl))

    lns3 = ax.plot(d.df.Date,d.df.fi_no_reinvest_Value, 'black',\
                                                label = "Fully invested strategy with no reinvestment annual return: {:.2%}"\
                                                .format(annualized_return_fi_nr))


    ax2 = ax.twinx()
    lns4 = ax2.plot(d.df.Date, d.df.Real_Price, 'orange', label = "Price (RHS): {:.2%}"\
                                                .format(annualized_price))

    lns = lns1+lns2+lns3+lns4
    labs = [l.get_label() for l in lns]
    ax.legend(lns, labs, loc='upper left', prop={'size': 15})

    ax.get_yaxis().set_major_formatter(
        tkr.FuncFormatter(lambda x, p: format(int(x), ',')))

    plt.title('Initial amount of $100,000 over ' + str(round(year_diff,2)) + ' years', fontdict = {'fontsize' : 25})

    fig.tight_layout() 
    plt.show()
    
    #PLOT 2
    fig, ax = plt.subplots(figsize=(12,8))
    ax.plot(d.df.Date, d.df.fi_Stock/d.df.fi_Value, 'b', label = "Fully invested")
    ax.plot(d.df.Date, d.df.fi_no_reinvest_Stock/d.df.fi_no_reinvest_Value, 'black', label = "Fully invested, no reinvestment")
    ax.plot(d.df.Date,d.df.shbl_Stock/d.df.shbl_Value, 'r', label = "Sell high/buy")
    plt.legend(loc="lower right", prop={'size': 20})
    plt.title('Strategy investment rate %', fontdict = {'fontsize' : 25})
    plt.show()

    #PLOT 3
    fig, ax = plt.subplots(figsize=(12,8))
    lns1 = ax.plot(d.df.Date,d.df.shbl_Value, 'b', label = "Sell high/buy low strategy invested (LHS)", alpha=0.3, linewidth = 1)
    lns3 = ax.plot(d.df.Date,d.df.shbl_Cash, '--b', label = "Cash available (LHS)", alpha=0.3, linewidth = 1)
    ax2 = ax.twinx()
    lns2 = ax2.plot(d.df.Date, d.df.Real_Price, 'orange', label = 'Price (RHS)', alpha=0.7, linewidth = 1)
    lns = lns1+lns2 + lns3
    labs = [l.get_label() for l in lns]
    ax.legend(lns, labs, loc='upper left', prop={'size': 20})

    ax.get_yaxis().set_major_formatter(
        tkr.FuncFormatter(lambda x, p: format(int(x), ',')))

    buy_points = d.df[d.df.shbl_Transaction =='B']
    sell_points = d.df[d.df.shbl_Transaction =='S']

    ax.scatter(buy_points.Date, buy_points.shbl_Value, c='green', s=200, linewidth=0, label = 'Buy')
    ax.scatter(sell_points.Date, sell_points.shbl_Value, c='red', s=200, linewidth=0, label = 'Sell')

    plt.title('Initial amount of 100,000 over ' + str(round(year_diff,2)) + ' years', fontdict = {'fontsize' : 25})

    fig.tight_layout() 
    plt.show()
    
def calculate_returns(day_skip = 4000):

    starting_amount = 100_000
    start = '1970-01-02'
    end = '2019-12-31'
    dividend_dates = [4,7,10,12]
    capital_dates = [4, 12]
    dividend_tax = 0.15        
    capital_tax = 0.15           
    capital_annual_yield = 0.001 
    annual_fund_fees = 0.00015   

    drop_pct_threshold = 0.2
    rise_pct_threshold = 0.6
    buy_pct = 0.4
    sell_pct = 0.1
    data  = download_data()

    #Get backtesting data object
    d = Data_Handler(data, starting_amount, start, end, dividend_dates, capital_dates, dividend_tax,
                     capital_tax, capital_annual_yield, annual_fund_fees)

    #Create backtesting data object.
    clean_data = Strategies(d, drop_pct_threshold, rise_pct_threshold, buy_pct, sell_pct)

    return_dict_fi = {}
    return_dict_shbl = {}
    
    starting_amount = clean_data.data.starting_amount
    
    for i in tqdm(range(0,len(clean_data.data.df), day_skip)):
    
        temp_d = deepcopy(clean_data)
        
        new_start_date = temp_d.data.df.Date.iloc[i]
        temp_d.data.df = temp_d.data.df[temp_d.data.df['Date'] >= new_start_date].reset_index()
        temp_d.data.max_price = temp_d.data.min_price = temp_d.data.df.iloc[0]['Price']

        temp_d.sell_high_buy_low_strat()
        temp_d.fully_invested_strat()
        
        ending_value_fi = temp_d.data.df.tail(1)['fi_Value'].iloc[0]
        ending_value_shbl = temp_d.data.df.tail(1)['shbl_Value'].iloc[0]

        ending_date = temp_d.data.df.tail(1)['Date'].iloc[0]
        
        year_diff = (ending_date - new_start_date) / datetime.timedelta(days=365)
        
        annualized_return_fi = (ending_value_fi / starting_amount) **(1/year_diff) - 1
        annualized_return_shbl = (ending_value_shbl / starting_amount) **(1/year_diff) - 1
        
        return_dict_fi[str(new_start_date)[:10]] = annualized_return_fi
        return_dict_shbl[str(new_start_date)[:10]] = annualized_return_shbl
    
    return_data = {'Fully_invested': return_dict_fi, 'Sell_high_buy_low': return_dict_shbl}
    return_data = pd.DataFrame.from_dict(return_data)
    fi_mean = round(np.mean(return_data.Fully_invested),3)
    shbl_mean = round(np.mean(return_data.Sell_high_buy_low),3)    
    sns.boxplot(data=return_data).set_title("Box plot based upon {} different starting dates"\
                                                .format(len(return_data)))
    
    plt.legend(loc = 'upper right', labels=['FI: mean ' + str(fi_mean), 'SHBL: mean ' \
                                                    + str(shbl_mean)], prop={'size': 9})
      
    return return_data
        

