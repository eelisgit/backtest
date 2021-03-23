import pandas as pd
import numpy as np

class Data_Handler():
    
        def __init__(self, df, starting_amount, start_date, end_date, dividend_payment_dates, capital_payment_dates,
                        dividend_tax=0.15, capital_tax=0.15, capital_annual_yield=0.001, annual_fund_fee = 0.00015, adjust_price = True):
                          
            self.df = df[(df['Date'] >= start_date) & (df['Date'] < end_date)].reset_index()
            if adjust_price:
                self.price_liquidity_adjustment()
            self.starting_amount= self.cash = starting_amount
            self.start_date = start_date
            self.end_date = end_date
            self.dividend_payment_dates = dividend_payment_dates
            self.capital_payment_dates = capital_payment_dates
            self.dividend_tax = dividend_tax
            self.capital_tax = capital_tax
            self.capital_period_yield = capital_annual_yield / len(capital_payment_dates)
            self.annual_fund_fee = annual_fund_fee
            self.max_price = self.min_price = self.df.iloc[0]['Price']
            self.shares = 0
            self.capital_invested = 0
            
            self.create_distribution_dates()
            
        def buy_stocks(self, index, row, buy_pct):
            investment_amount = self.cash * buy_pct
            new_shares = np.floor(investment_amount / row.Price)
            investment_amount_achieved = new_shares * row.Price
            self.capital_invested += investment_amount_achieved
            self.cash = self.cash - investment_amount_achieved
            self.shares += new_shares

            self.max_price = row.Price
            self.df.loc[index, 'Transaction'] = 'B'
            
        def sell_stocks(self, index, row, sell_pct):
        
            if self.shares > 0:
                shares_sold = np.floor(self.shares * sell_pct)
                cost_basis = self.capital_invested / self.shares
                capital_tax_amount = max((row.Price - cost_basis) * shares_sold * self.capital_tax, 0)
                money_received = shares_sold*row.Price - capital_tax_amount
                #self.capital_invested -= shares_sold*row.Price
                self.capital_invested -= shares_sold*cost_basis
                self.cash = self.cash + money_received
                self.shares = self.shares - shares_sold
                self.df.loc[index, 'Capital_Gains_Tax'] = capital_tax_amount
            
            self.min_price = row.Price
            self.df.loc[index, 'Transaction'] = 'S'
   
        def add_column(self, data, name):
            self.df[name] = data
            
        def price_liquidity_adjustment(self):
            #S&P500 price now is around 4k whereas most index fund prices are around a magnitude smaller. Without this adjustment we would keep
            # more cash than in reality due to trading friction caused by using the higher SP500 price in the backtest.
            self.df['Real_Price'] = self.df['Price']
            self.df['Price'] = self.df['Price'] / 10
            
            self.df['Real_Dividend'] = self.df['Dividend']
            self.df['Dividend'] = self.df['Dividend'] / 10
            
        def create_distribution_dates(self):
            dividend_fraction_dict = {4:4/12, 7:3/12, 10:3/12, 12:2/12}
            self.df['Period_Dividend'] = 0
            self.df['Capital_Yield'] = 0
            self.df['Fund_Fee'] = 0
            size = len(self.df)
            
            for index, row in self.df.iterrows():
                if index != size-1:
                    month = self.df.Date.iloc[index].month
                    next_month = self.df.Date.iloc[index + 1].month
                    year = self.df.Date.iloc[index].year
                    next_year = self.df.Date.iloc[index + 1].year
                    if (month in self.capital_payment_dates) & (month != next_month):
                        self.df.Capital_Yield.iloc[index] = self.capital_period_yield     
                    if (month in self.dividend_payment_dates) & (month != next_month):
                        self.df.Period_Dividend.iloc[index] = dividend_fraction_dict[month] * self.df.Dividend.iloc[index]  
                    if year != next_year:
                        self.df.Fund_Fee.iloc[index] = self.annual_fund_fee