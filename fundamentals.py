from __future__ import division
import requests
import pandas as pd
from bs4 import BeautifulSoup as bs
import re
import os
import time

# metric = ['Market Cap', 'P/E', 'EPS (ttm)', 'Dividend', 'Dividend %', 'Shs Outstand', 'Price', 'Cash/sh']
# metrics_2 = ['Beta', 'Total Debt']

class Fundamentals(object):
    next_idx = 0

    URLS = ["http://www.marketwatch.com/investing/stock/{}", 
            "http://www.marketwatch.com/investing/stock/{}/financials", 
            "http://www.marketwatch.com/investing/stock/{}/financials/cash-flow",
            "https://finance.yahoo.com/quote/{}/key-statistics",
            "http://finviz.com/quote.ashx?t={}",
            "https://finance.yahoo.com/quote/{}/balance-sheet",
            "https://finance.yahoo.com/quote/{}?p={}"]

    KEYS = ["Ticker", \
            "Previous Close", \
            "Volume", \
            "Market Cap", \
            "Total Debt", \
            "Net Receivables", \
            "Inventory", \
            "Property Plant and Equipment", \
            "Total Liabilities", \
            "Shares Outstanding"
            "Beta", \
            "PE Ratio (TTM)", \
            "EPS (TTM)", \
            "Dividend", \
            "Dividend %", \
            "Cash/sh"]

    CALC_DATA = {"Book Value": "", "NAV": ""}
    # keys are case sensitive - match data on the mw financials page

    def __init__(self, risk_free_rate, market_return, ticker, logger):
        self.name = "Fundamentals"
        self.logger = logger
        self.ticker = ticker
        self.risk_free_rate = risk_free_rate # Return on 10 year US Treasury Bonds
        self.market_return = market_return # 3yr Return on the SPY (S&P 500 tracker)
        self.mw_url = "" # URL with appended ticker
        self.wacc = 0
        self.growth_rate = 0
        self.price_diff = 0
        self.price = 0
        self.df = pd.DataFrame(columns=self.KEYS)
        self.data = dict.fromkeys(self.KEYS, 0.0)

    def yahooScrapper(self):
        self.yahooSummaryScrapper()
        self.yahooKeyStatisticsScrapper()
        self.yahooBalanceSheetScrapper()
        self.addToDb()

    def addToDb(self):
        l_df = pd.DataFrame(self.data, index=[self.next_idx])
        self.next_idx += 1
        self.df = self.df.append(l_df, sort=False)

    def yahooSummaryScrapper(self):
        try:
            ystock_url = self.URLS[6].format(self.ticker, self.ticker)
            soup = bs(requests.get(ystock_url).content, features='html5lib')

            self.data["Ticker"] = self.ticker

            to_scrap = "Volume"
            scraped_data = soup.find(text = to_scrap).find_next().text
            self.data[to_scrap] = self.raw_to_num(scraped_data)

            to_scrap = "Previous Close"
            scraped_data = soup.find(text = to_scrap).find_next().text
            self.data[to_scrap] = self.raw_to_num(scraped_data)

            to_scrap = "Market Cap"
            scraped_data = soup.find(text = to_scrap).find_next().text
            self.data[to_scrap] = self.raw_to_floats(scraped_data)

            to_scrap = "PE Ratio (TTM)"
            scraped_data = soup.find(text = to_scrap).find_next().text
            self.data[to_scrap] = self.raw_to_num(scraped_data)

            to_scrap = "EPS (TTM)"
            scraped_data = soup.find(text = to_scrap).find_next().text
            self.data[to_scrap] = self.raw_to_num(scraped_data)
        except:
            pass

    def yahooKeyStatisticsScrapper(self):
        try:
            ystock_url = self.URLS[3].format(self.ticker)
            soup = bs(requests.get(ystock_url).content, features='html5lib')
        except:
            self.logger.info("[yahooKeyStatisticsScrapper] Error souping %s" % ystock_url)

        try:
            # Total Debt
            to_scrap = "Total Debt"
            scraped_data = soup.find(text = to_scrap).find_next(class_='Fz(s) Fw(500) Ta(end)').text
            self.data[to_scrap] = self.raw_to_floats(scraped_data)

            # Shares Outstanding
            to_scrap = "Shares Outstanding"
            scraped_data = soup.find(text = to_scrap).find_next(class_='Fz(s) Fw(500) Ta(end)').text
            self.data[to_scrap] = self.raw_to_floats(scraped_data)
            
            # Beta
            to_scrap = "Beta"
            scraped_data = soup.find(text = to_scrap).find_next(class_='Fz(s) Fw(500) Ta(end)').text
            self.beta = float(scraped_data) 
            self.data[to_scrap] = self.beta
        except:
            self.logger.info("[yahooKeyStatisticsScrapper] Error scraping %s" % to_scrap)

        try:
            self.cost_of_eq = self.risk_free_rate + self.beta * (self.market_return - self.risk_free_rate)
        except:
            self.logger.info("[yahoo_scraper] Error in cost_of_eq calc")

    def yahooBalanceSheetScrapper(self):
        try:
            ystock_url = self.URLS[5].format(self.ticker)
            soup = bs(requests.get(ystock_url).content, features='html5lib')
        except:
            self.logger.info("[yahooBalanceSheetScrapper] Error souping %s" % ystock_url)

        try:            
            # Cash And Cash Equivalents
            to_scrap = "Cash And Cash Equivalents"
            scraped_data = soup.find(text = to_scrap).find_next(class_='Fz(s) Ta(end) Pstart(10px)').text            
            self.data[to_scrap] = self.raw_to_num(scraped_data, multiplier=1000)

            # Net Receivables
            to_scrap = "Net Receivables"
            scraped_data = soup.find(text = to_scrap).find_next(class_='Fz(s) Ta(end) Pstart(10px)').text            
            self.data[to_scrap] = self.raw_to_num(scraped_data, multiplier=1000)

            # Inventory
            to_scrap = "Inventory"
            scraped_data = soup.find(text = to_scrap).find_next(class_='Fz(s) Ta(end) Pstart(10px)').text
            self.data[to_scrap] = self.raw_to_num(scraped_data, multiplier=1000)

            # Property Plant and Equipment
            to_scrap = "Property Plant and Equipment"
            scraped_data = soup.find(text = to_scrap).find_next(class_='Fz(s) Ta(end) Pstart(10px)').text
            self.data[to_scrap] = self.raw_to_num(scraped_data, multiplier=1000)

            # Total Liabilities
            to_scrap = "Total Liabilities"                                         
            scraped_data = soup.find(text = to_scrap).find_next(class_='Fw(b) Fz(s) Ta(end) Pb(20px)').text
            self.data[to_scrap] = self.raw_to_num(scraped_data, multiplier=1000)
        except:
            self.logger.info("[yahooBalanceSheetScrapper] Error scraping %s" % to_scrap)

        try:
            self.data["NET-NET"] = (self.data["Cash And Cash Equivalents"] + \
                                            0.75 * self.data["Net Receivables"] + \
                                            0.50 * self.data["Inventory"] + \
                                            self.data["Property Plant and Equipment"] - \
                                            self.data["Total Liabilities"]) / self.data["Shares Outstanding"]
        except:
            self.logger.info("[yahooBalanceSheetScrapper] Error in NET-NET calc")

    def raw_to_floats(self, num): # convert to floats as numbers on MW are represented with a "M" or "B"            
        # multiplier = 1/1000000
        multiplier = 1

        if "M" in num:
            multiplier = 1000000
        if "B" in num:
            multiplier = 1000000000
        if "T" in num:
            multiplier = 1000000000000

        processor = re.compile(r'[^\d.]+')
        try:
            processed_num = float(processor.sub('', num))
            n = processed_num * multiplier
            return n
        except ValueError:
            return 0.0

    def raw_to_num(self, num, multiplier=1): # convert to floats as numbers on MW are represented with a "M" or "B"            
        processor = re.compile(r'[^\d.]+')
        try:
            processed_num = float(processor.sub('', num))
            n = processed_num * multiplier
            return n
        except ValueError:
            return 0.0

    # def y_scraper(self): # Use CAPM formula to calculate cost of equity: Cost of Equity = Rf + Beta(Rm-Rf)
    #     ystock_url = Fundamentals.URLS[3].format(self.ticker)
    #     scraped_data = {"Beta": "", "Total Debt": ""}

    #     try:
    #         soup = bs(requests.get(ystock_url).content, features='html5lib')
    #         scraped_data["Total Debt"] = soup.find(text = "Total Debt").find_next(class_='Fz(s) Fw(500) Ta(end)').text
    #         self.data["Total Debt"] = self.raw_to_floats(scraped_data["Total Debt"])

    #         scraped_data["Beta"] = soup.find(text = "Beta").find_next(class_='Fz(s) Fw(500) Ta(end)').text
    #         self.beta = float(scraped_data["Beta"]) #improve readability of the below formula, dont need this variable.
    #         self.data["Beta"] = self.beta

    #         self.cost_of_eq = self.risk_free_rate + self.beta * (self.market_return - self.risk_free_rate)
    #     except:
    #         print("Error in y_scraper function")

    # def statement_scraper(self, url, *line_items): 
    #     statement_url = url.format(self.ticker)
    #     r = requests.get(statement_url)
    #     soup = bs(r.text, "lxml")

    #     for line_item in line_items:
    #         target_list = []
    #         try:
    #             target = soup.find("td", text=line_item).parent
    #             target_row = target.findAll("td", {"class" : "valueCell"})
    #             for cell in target_row:
    #                 num_in_MMs = self.raw_to_floats(cell.text)
    #                 target_list.append(num_in_MMs)
    #             yield target_list

    #         except AttributeError: # Some elements have a "+" icon next to them and searching by text won't work
    #             table_rows = soup.findAll("td", {"class" : "rowTitle"})
    #             for row in table_rows:
    #                 if line_item.lower() in row.text.lower():
    #                     _match = re.search(r"" + line_item + "$",row.text) # search for the line item in the results of our scrape
    #                     if _match:
    #                         outer_row = row.parent

    #                         _row = outer_row.findAll("td", {"class" : "valueCell"}) # Create a list with the FCF over the past four years
    #                         _list = []

    #                         for amount in _row:
    #                             amount = self.raw_to_floats(amount.text)
    #                             _list.append(amount)
    #                         yield _list

    # def get_growth_rate(self, trend_list):
    #     #Calculate the growth rate of a list of line items from 2012 - 2016
    #     trend_list = [num for num in trend_list if num != 0]
    #     growth_sum = 0
    #     for a, b in zip(trend_list[::1], trend_list[1::1]):
    #         growth_sum += (b - a) / a

    #     growth_rate = growth_sum/(len(trend_list)-1)
    #     return growth_rate


    # def get_cf(self):        
    #     cf_generator = self.statement_scraper(self.URLS[2], "Free Cash Flow")
    #     try:
    #         cash_flow = next(cf_generator)
    #         cf_growth_rate = self.get_growth_rate(cash_flow)
    #         self.growth_rate = cf_growth_rate
    #         self.data["Cash Flow"] = cash_flow
    #         self.data["CF Growth Rate"] = "{0:.2f}%".format(cf_growth_rate * 100)
    #     except:
    #         print("Error in get_cf function")

    # def get_dcf(self):
    #     try:
    #         self.cf_list = []
    #         self.discounted_cf_list = []
    #         CF0 = self.data["Cash Flow"][0]
    #         for i in range(1, 6):
    #             cf = CF0 * (1.05 ** i)
    #             # print "CF0[%d]: %f, cf: %f" % (i, CF0, cf)
    #             discounted = cf / ((1 + self.wacc) ** i)
    #             # print discounted
    #             self.cf_list.append(cf)
    #             self.discounted_cf_list.append(discounted)
          
    #         # TCF = (cf_list[-1] * wacc^5)/ (wacc - self.growth_rate)
    #         # TCF = (cf_list[-1] * self.wacc**5)/ (self.wacc - self.growth_rate)
    #         # print "CFn: %f, WACC: %f, growth_rate: %f" % (cf_list[-1], self.wacc, self.growth_rate)
    #         self.TCF = self.cf_list[-1] / (self.wacc - self.growth_rate)
    #         self.discounted_cf_list.append(self.TCF / ((1 + self.wacc) ** i))
    #         # print "TCF:%f, CFn: %f, WACC: %f, growth_rate: %f" % (TCF, cf_list[-1], self.wacc, self.growth_rate)
    #         # print cf_list
    #         # print discounted_cf_list
    #         self.PV = sum(self.discounted_cf_list)
    #         # print "PV: " + str(PV)
    #         self.price_per_share = self.PV / self.data["Shs Outstand"]
    #         self.price = self.raw_to_num(self.data["Price"])
    #         # print self.price
    #         rate = self.price_per_share / self.price
    #         self.price_diff = (rate - 1) * 100
    #     except:
    #         print("Error in get_dcf function")

    # def mw_scraper(self):
    #     tickers = []
    #     tickers.append(self.ticker)
    #     df = pd.DataFrame(index=tickers, columns=metric)
    #     try:
    #         mw_url = Fundamentals.URLS[4].format(self.ticker)
    #         soup = bs(requests.get(mw_url).content, features='html5lib') 
    #         for m in df.columns:
    #             df.loc[self.ticker,m] = soup.find(text = m).find_next(class_='snapshot-td2').text
    #             self.data[m] = df.loc[self.ticker,m]
                
    #             letter_check = re.search('[a-zA-Z]', self.data[m]) # Check for items that are not pure numbers -e.g "6.6BN"
    #             if letter_check is not None:
    #                 self.data[m] = self.raw_to_floats(self.data[m])
    #     except Exception as e:
    #         print (self.ticker, 'not found')

    # # Need to be called first
    # def calc_wacc(self):
    #     self.y_scraper()
    #     self.mw_scraper()
    #     is_generator = self.statement_scraper(self.URLS[1], "Gross Interest Expense", "Income Tax", "Pretax Income") # income statement generator
        
    #     try:
    #         interest_list = next(is_generator)
    #         int_expense = interest_list[-1]

    #         tax_list = next(is_generator)
    #         inc_tax = tax_list[-1]

    #         pretax_inc_list = next(is_generator)
    #         pretax_inc = pretax_inc_list[-1]

    #         if pretax_inc < 1 or inc_tax < 1: # Adjusts for smaller companies who may temporarily have negative income or tax benefits
    #             tax_rate = 0.35
    #         else:
    #             tax_rate = inc_tax/pretax_inc

    #         self.cost_of_debt = int_expense/self.data["Total Debt"]

    #         weighted_coe = (float(self.data["Market Cap"])/(float(self.data["Total Debt"]) + float(self.data["Market Cap"]))) * self.cost_of_eq
    #         weighted_cod = (float(self.data["Total Debt"])/(float(self.data["Market Cap"]) + float(self.data["Total Debt"]))) * self.cost_of_debt * (1 - tax_rate)

    #         self.wacc = weighted_coe + weighted_cod 
    #         self.data["WACC"] = "{0:.2f}%".format(self.wacc * 100)
    #     except:
    #         print("Error in calc_wacc function")
        
    def print_data(self):
        print("The Weighted Average Cost of Capital for {0:s} is {1:.2f}%. Other key stats are listed below (Total Debt and Market Cap in MM's)\n\n".format(self.ticker, (self.wacc* 100)))
        print self.df
        # for key in self.SUMMARY_DATA:
        #     print("{} : {}".format(key, self.data[key]))
    
    def print_calcs(self):
        print("{} : {}".format("PV", self.PV))
        print("{} : {}".format("Price-per-Share", self.price_per_share))
        print("{} : {}%".format("Price-Diff", self.price_diff))