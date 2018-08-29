from __future__ import division
import requests
import pandas as pd
from bs4 import BeautifulSoup as bs
import re
import os
import time

metric = ['Market Cap', 'P/E', 'EPS (ttm)', 'Dividend', 'Dividend %', 'Shs Outstand', 'Price', 'Cash/sh']
# metrics_2 = ['Beta', 'Total Debt']

class Fundamentals(object):
    URLS = ["http://www.marketwatch.com/investing/stock/{}", 
            "http://www.marketwatch.com/investing/stock/{}/financials", 
            "http://www.marketwatch.com/investing/stock/{}/financials/cash-flow",
            "https://finance.yahoo.com/quote/{}/key-statistics",
            "http://finviz.com/quote.ashx?t={}",
            "https://finance.yahoo.com/quote/{}/balance-sheet"]
    SUMMARY_DATA = {"Market Cap":" ", "P/E": " ", "EPS (ttm)":" ", "Dividend": " ", "Dividend %": " ", "Shs Outstand": " ", "Price": " ", "Cash/sh": " ",
                    "Beta": "", "Total Debt": "", "Net Receivables": "", "Inventory": "", "Property Plant and Equipment": "", "Total Liabilities": ""}
     # keys are case sensitive - match data on the mw financials page


    def __init__(self, risk_free_rate, market_return, ticker):
        self.name = "Fundamentals"
        self.ticker = ticker
        self.risk_free_rate = risk_free_rate # Return on 10 year US Treasury Bonds
        self.market_return = market_return # 3yr Return on the SPY (S&P 500 tracker)
        self.mw_url = "" # URL with appended ticker
        self.wacc = 0
        self.growth_rate = 0
        self.price_diff = 0
        self.price = 0

    def yahoo_scrapper(self):
        ystock_url = Fundamentals.URLS[3].format(self.ticker)
        scraped_data = {"Beta": "", "Total Debt": "", "Net Receivables": "", "Inventory": "", "Property Plant and Equipment": "", "Total Liabilities": ""}

        try:
            soup = bs(requests.get(ystock_url).content, features='html5lib')
        except:
            print("Error in yahoo_scraper function - souping")

        try:            
            # Total Debt
            to_scrap = "Total Debt"
            scraped_data[to_scrap] = soup.find(text = to_scrap).find_next(class_='Fz(s) Fw(500) Ta(end)').text
            self.SUMMARY_DATA[to_scrap] = self.raw_to_floats(scraped_data[to_scrap])
        except:
            print("Error in yahoo_scraper function - Total Dept")

        try:
            # Beta
            to_scrap = "Beta"
            scraped_data[to_scrap] = soup.find(text = to_scrap).find_next(class_='Fz(s) Fw(500) Ta(end)').text
            self.beta = float(scraped_data[to_scrap]) 
            self.SUMMARY_DATA[to_scrap] = self.beta
        except:
            print("Error in yahoo_scraper function - Beta")

        try:
            ystock_url = Fundamentals.URLS[5].format(self.ticker)
            soup = bs(requests.get(ystock_url).content, features='html5lib')
        except:
            print("Error in yahoo_scraper function - 2nd souping")

        try:
            # Net Receivables
            to_scrap = "Net Receivables"
            scraped_data[to_scrap] = soup.find(text = to_scrap).find_next(class_='"Fz(s) Ta(end) Pstart(10px)').text
            self.SUMMARY_DATA[to_scrap] = self.raw_to_num(scraped_data[to_scrap])
        except:
            print("Error in yahoo_scraper function - Net Receivables")    

        try:
            # Inventory
            to_scrap = "Inventory"
            scraped_data[to_scrap] = soup.find(text = to_scrap).find_next(class_='"Fz(s) Ta(end) Pstart(10px)').text
            self.SUMMARY_DATA[to_scrap] = self.raw_to_num(scraped_data[to_scrap])
        except:
            print("Error in yahoo_scraper function - Inventory")

        try:
            # Property Plant and Equipment
            to_scrap = "Property Plant and Equipment"
            scraped_data[to_scrap] = soup.find(text = to_scrap).find_next(class_='"Fz(s) Ta(end) Pstart(10px)').text
            self.SUMMARY_DATA[to_scrap] = self.raw_to_num(scraped_data[to_scrap])
        except:
            print("Error in yahoo_scraper function - Property Plant and Equipment")

        try:
            # Total Liabilities
            to_scrap = "Total Liabilities"
            scraped_data[to_scrap] = soup.find(text = to_scrap).find_next(class_='"Fz(s) Ta(end) Pstart(10px)').text
            self.SUMMARY_DATA[to_scrap] = self.raw_to_num(scraped_data[to_scrap])
        except:
            print("Error in yahoo_scraper function - Total Liabilities")

        try:
            self.cost_of_eq = self.risk_free_rate + self.beta * (self.market_return - self.risk_free_rate)
        except:
            print("Error in yahoo_scraper function - cost_of_eq calc")

    def y_scraper(self): # Use CAPM formula to calculate cost of equity: Cost of Equity = Rf + Beta(Rm-Rf)
        ystock_url = Fundamentals.URLS[3].format(self.ticker)
        scraped_data = {"Beta": "", "Total Debt": ""}

        try:
            soup = bs(requests.get(ystock_url).content, features='html5lib')
            scraped_data["Total Debt"] = soup.find(text = "Total Debt").find_next(class_='Fz(s) Fw(500) Ta(end)').text
            self.SUMMARY_DATA["Total Debt"] = self.raw_to_floats(scraped_data["Total Debt"])

            scraped_data["Beta"] = soup.find(text = "Beta").find_next(class_='Fz(s) Fw(500) Ta(end)').text
            self.beta = float(scraped_data["Beta"]) #improve readability of the below formula, dont need this variable.
            self.SUMMARY_DATA["Beta"] = self.beta

            self.cost_of_eq = self.risk_free_rate + self.beta * (self.market_return - self.risk_free_rate)
        except:
            print("Error in y_scraper function")


    def raw_to_floats(self, num): # convert to floats as numbers on MW are represented with a "M" or "B"            
        multiplier = 1/1000000

        if "M" in num:
            multiplier = 1
        if "B" in num:
            multiplier = 1000 

        processor = re.compile(r'[^\d.]+')
        try:
            processed_num = float(processor.sub('', num))
            n = processed_num * multiplier
            return n
        except ValueError:
            return 0.0

    def raw_to_num(self, num): # convert to floats as numbers on MW are represented with a "M" or "B"            
        processor = re.compile(r'[^\d.]+')
        try:
            processed_num = float(processor.sub('', num))
            n = processed_num
            return n
        except ValueError:
            return 0.0

    def mw_scraper(self):
        tickers = []
        tickers.append(self.ticker)
        df = pd.DataFrame(index=tickers, columns=metric)
        try:
            mw_url = Fundamentals.URLS[4].format(self.ticker)
            soup = bs(requests.get(mw_url).content, features='html5lib') 
            for m in df.columns:
                df.loc[self.ticker,m] = soup.find(text = m).find_next(class_='snapshot-td2').text
                self.SUMMARY_DATA[m] = df.loc[self.ticker,m]
                
                letter_check = re.search('[a-zA-Z]', self.SUMMARY_DATA[m]) # Check for items that are not pure numbers -e.g "6.6BN"
                if letter_check is not None:
                    self.SUMMARY_DATA[m] = self.raw_to_floats(self.SUMMARY_DATA[m])
        except Exception as e:
            print (self.ticker, 'not found')


    def statement_scraper(self, url, *line_items): 
        statement_url = url.format(self.ticker)
        r = requests.get(statement_url)
        soup = bs(r.text, "lxml")

        for line_item in line_items:
            target_list = []
            try:
                target = soup.find("td", text=line_item).parent
                target_row = target.findAll("td", {"class" : "valueCell"})
                for cell in target_row:
                    num_in_MMs = self.raw_to_floats(cell.text)
                    target_list.append(num_in_MMs)
                yield target_list

            except AttributeError: # Some elements have a "+" icon next to them and searching by text won't work
                table_rows = soup.findAll("td", {"class" : "rowTitle"})
                for row in table_rows:
                    if line_item.lower() in row.text.lower():
                        _match = re.search(r"" + line_item + "$",row.text) # search for the line item in the results of our scrape
                        if _match:
                            outer_row = row.parent

                            _row = outer_row.findAll("td", {"class" : "valueCell"}) # Create a list with the FCF over the past four years
                            _list = []

                            for amount in _row:
                                amount = self.raw_to_floats(amount.text)
                                _list.append(amount)
                            yield _list


    def get_growth_rate(self, trend_list):
        #Calculate the growth rate of a list of line items from 2012 - 2016
        trend_list = [num for num in trend_list if num != 0]
        growth_sum = 0
        for a, b in zip(trend_list[::1], trend_list[1::1]):
            growth_sum += (b - a) / a

        growth_rate = growth_sum/(len(trend_list)-1)
        return growth_rate


    def get_cf(self):        
        cf_generator = self.statement_scraper(self.URLS[2], "Free Cash Flow")
        try:
            cash_flow = next(cf_generator)
            cf_growth_rate = self.get_growth_rate(cash_flow)
            self.growth_rate = cf_growth_rate
            self.SUMMARY_DATA["Cash Flow"] = cash_flow
            self.SUMMARY_DATA["CF Growth Rate"] = "{0:.2f}%".format(cf_growth_rate * 100)
        except:
            print("Error in get_cf function")

    def get_dcf(self):
        try:
            self.cf_list = []
            self.discounted_cf_list = []
            CF0 = self.SUMMARY_DATA["Cash Flow"][0]
            for i in range(1, 6):
                cf = CF0 * (1.05 ** i)
                # print "CF0[%d]: %f, cf: %f" % (i, CF0, cf)
                discounted = cf / ((1 + self.wacc) ** i)
                # print discounted
                self.cf_list.append(cf)
                self.discounted_cf_list.append(discounted)
          
            # TCF = (cf_list[-1] * wacc^5)/ (wacc - self.growth_rate)
            # TCF = (cf_list[-1] * self.wacc**5)/ (self.wacc - self.growth_rate)
            # print "CFn: %f, WACC: %f, growth_rate: %f" % (cf_list[-1], self.wacc, self.growth_rate)
            self.TCF = self.cf_list[-1] / (self.wacc - self.growth_rate)
            self.discounted_cf_list.append(self.TCF / ((1 + self.wacc) ** i))
            # print "TCF:%f, CFn: %f, WACC: %f, growth_rate: %f" % (TCF, cf_list[-1], self.wacc, self.growth_rate)
            # print cf_list
            # print discounted_cf_list
            self.PV = sum(self.discounted_cf_list)
            # print "PV: " + str(PV)
            self.price_per_share = self.PV / self.SUMMARY_DATA["Shs Outstand"]
            self.price = self.raw_to_num(self.SUMMARY_DATA["Price"])
            # print self.price
            rate = self.price_per_share / self.price
            self.price_diff = (rate - 1) * 100
        except:
            print("Error in get_dcf function")

    def calc_wacc(self):
        self.y_scraper()
        self.mw_scraper()
        is_generator = self.statement_scraper(self.URLS[1], "Gross Interest Expense", "Income Tax", "Pretax Income") # income statement generator
        
        try:
            interest_list = next(is_generator)
            int_expense = interest_list[-1]

            tax_list = next(is_generator)
            inc_tax = tax_list[-1]

            pretax_inc_list = next(is_generator)
            pretax_inc = pretax_inc_list[-1]

            if pretax_inc < 1 or inc_tax < 1: # Adjusts for smaller companies who may temporarily have negative income or tax benefits
                tax_rate = 0.35
            else:
                tax_rate = inc_tax/pretax_inc

            self.cost_of_debt = int_expense/self.SUMMARY_DATA["Total Debt"]

            weighted_coe = (float(self.SUMMARY_DATA["Market Cap"])/(float(self.SUMMARY_DATA["Total Debt"]) + float(self.SUMMARY_DATA["Market Cap"]))) * self.cost_of_eq
            weighted_cod = (float(self.SUMMARY_DATA["Total Debt"])/(float(self.SUMMARY_DATA["Market Cap"]) + float(self.SUMMARY_DATA["Total Debt"]))) * self.cost_of_debt * (1 - tax_rate)

            self.wacc = weighted_coe + weighted_cod 
            self.SUMMARY_DATA["WACC"] = "{0:.2f}%".format(self.wacc * 100)
        except:
            print("Error in calc_wacc function")
        
    def print_data(self):
        print("The Weighted Average Cost of Capital for {0:s} is {1:.2f}%. Other key stats are listed below (Total Debt and Market Cap in MM's)".format(self.ticker, (self.wacc* 100)))
        for key in self.SUMMARY_DATA:
            print("{} : {}".format(key, self.SUMMARY_DATA[key]))
    
    def print_calcs(self):
        print("{} : {}".format("PV", self.PV))
        print("{} : {}".format("Price-per-Share", self.price_per_share))
        print("{} : {}%".format("Price-Diff", self.price_diff))