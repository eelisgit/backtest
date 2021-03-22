from copy import deepcopy
import pandas as pd
import numpy as np

class Strategies():
    
        def __init__(self, data, drop_pct_threshold, rise_pct_threshold, buy_pct, sell_pct):
            self.data = data
            self.drop_pct_threshold = drop_pct_threshold
            self.rise_pct_threshold = rise_pct_threshold
            self.buy_pct = buy_pct
            self.sell_pct = sell_pct
            
        def distribution_and_fees(self, data, row, index):
            #Get capital gains at end of the day of relevant period.
            if row.Capital_Yield > 0:
                capital_gains = row.Capital_Yield * data.shares*row.Price*(1-data.capital_tax)
                data.cash += capital_gains
                data.df.loc[index, 'Capital_Distribution'] = capital_gains

            #Get dividends at end of the day of relevant period.
            if row.Period_Dividend > 0:
                dividend_cash = row.Period_Dividend * data.shares * (1-data.dividend_tax)
                data.cash += dividend_cash
                data.df.loc[index, 'Total_Dividends'] = dividend_cash

            #Pay fund fees at end of the day at end of year.
            if row.Fund_Fee > 0:
                fund_fee = row.Fund_Fee * data.shares*row.Price
                data.cash -= fund_fee
                data.df.loc[index, 'Fund_Annual_Cost'] = fund_fee  
        
        def run_strategies(self):
        
            self.fully_invested_strat()
            self.fully_invested_strat(reinvest = False)
            self.sell_high_buy_low_strat()
            
        def add_extra_columns(self, data):
        
            data.df['Transaction'] = 0
            data.df['Total_Dividends'] = 0
            data.df['Capital_Distribution'] = 0
            data.df['Fund_Annual_Cost'] = 0
            data.df['Capital_Gains_Tax'] = 0
            
            return data
            
        def log_strategy(self, data, strategy_name):
        
            self.data.add_column(data.df[strategy_name], strategy_name + '_Value')
            self.data.add_column(data.df['Cash'], strategy_name + '_Cash')
            self.data.add_column(data.df['Stock'], strategy_name + '_Stock')
            self.data.add_column(data.df['Transaction'], strategy_name + '_Transaction')
            self.data.add_column(data.df['Total_Dividends'], strategy_name + '_Total_Dividends')
            self.data.add_column(data.df['Capital_Distribution'], strategy_name +'_Capital_Distribution')
            self.data.add_column(data.df['Fund_Annual_Cost'], strategy_name +'_Fund_Annual_Cost')  
            self.data.add_column(data.df['Capital_Gains_Tax'], strategy_name +'Capital_Gains_Tax')              
        
        def fully_invested_strat(self, strategy_name = 'fi', reinvest = True):
        
            #Make copy to avoid changing attributes of original data object.
            data = deepcopy(self.data)
            data = self.add_extra_columns(data)
            
            if reinvest != True:
                strategy_name = strategy_name + '_no_reinvest'
                
            data.shares = np.floor(data.cash / data.min_price)
            investment = data.shares * data.min_price #Min price = initial price
            data.cash -= investment
            
            for index, row in data.df.iterrows():
                
                if reinvest == True:
                    new_shares = np.floor(data.cash / row.Price)
                    if new_shares > 0:
                        data.buy_stocks(index, row, 1.00) #1.00 = buy stocks with all cash.
                    
                self.distribution_and_fees(data, row, index)
                
                data.df.loc[index, strategy_name] = data.shares*row.Price + data.cash
                data.df.loc[index, 'Cash'] = data.cash
                data.df.loc[index, 'Stock'] = data.shares*row.Price
                
            #Add new series to the original data object
            self.log_strategy(data, strategy_name)
            
        def sell_high_buy_low_strat(self, strategy_name = 'shbl'):
            
            #Make copy to avoid changing attributes of original data object.
            data = deepcopy(self.data)
            data = self.add_extra_columns(data)
            
            #Loop through rows
            for index, row in data.df.iterrows():
                
                #Update max price
                if row.Price > data.max_price:
                    data.max_price = row.Price
                #Update min price
                if row.Price < data.min_price:
                    data.min_price = row.Price
                    
                #Find percentage decrease from peak
                price_drop = data.max_price - row.Price
                pct_decrease = (data.max_price - row.Price) / data.max_price
                
                #Find percentage increase from trough
                price_increase = row.Price - data.min_price
                pct_increase = (row.Price - data.min_price) / data.min_price
                
                #Buy stock if price has dropped enough
                if pct_decrease >= self.drop_pct_threshold:
                    data.buy_stocks(index, row, self.buy_pct)
                    
                #Sell stock if it has risen enough
                if pct_increase >= self.rise_pct_threshold:
                    data.sell_stocks(index, row, self.sell_pct)                   
                    
                self.distribution_and_fees(data, row, index)
                    
                #Update value for the day.    
                value = data.cash + data.shares*row.Price
                data.df.loc[index, strategy_name] = value
                data.df.loc[index, 'Cash'] = data.cash
                data.df.loc[index, 'Stock'] = data.shares*row.Price
                       
            #Add new series to the original data object
            self.log_strategy(data, strategy_name)
            
        
                