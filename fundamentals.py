from __future__ import division
import requests
import pandas as pd
from bs4 import BeautifulSoup as bs
import os
import time
import urllib2
from utils import *
# from simple_requests import Requests

# metric = ['Market Cap', 'P/E', 'EPS (ttm)', 'Dividend', 'Dividend %', 'Shs Outstand', 'Price', 'Cash/sh']
# metrics_2 = ['Beta', 'Total Debt']

class Fundamentals(object):
    next_idx = 0

    URLS = ["https://www.marketwatch.com/investing/stock/{}", 
            "https://www.marketwatch.com/investing/stock/{}/financials", 
            "https://www.marketwatch.com/investing/stock/{}/financials/cash-flow",
            "https://finance.yahoo.com/quote/{}/key-statistics",
            "https://finviz.com/quote.ashx?t={}",
            "https://finance.yahoo.com/quote/{}/balance-sheet",
            "https://finance.yahoo.com/quote/{}?p={}",
            "https://finance.yahoo.com/quote/{}/profile?p={}"]

    KEYS = ["Ticker", \
            "Sector", \
            "Industry", \
            "Previous Close", \
            "Volume", \
            "Market Cap", \
            "Enterprise Value", \
            "Total Debt", \
            "Net Receivables", \
            "Inventory", \
            "Property Plant and Equipment", \
            "Total Assets", \
            "Intangible Assets", \
            "Total Liabilities", \
            "Shares Outstanding", \
            "Beta (3y)", \
            "PE Ratio (TTM)", \
            "Price/Sales", \
            "EPS (TTM)", \
            "Dividend", \
            "Dividend %", \
            "Cash/sh", \
            "Cash And Cash Equivalents", \
            "FCF", \
            "NAV", \
            "NAV%", \
            "NET-NET", \
            "NET-NET%", \
            "EY", \
            "EV/FCF", \
            "Tangible Book Value", \
            "Price/Tangible Book Value", \
            "WACC%", \
            "CFGR%"]

    def __init__(self, risk_free_rate, market_return, logger):
        self.name = "Fundamentals"
        self.logger = logger
        self.risk_free_rate = risk_free_rate # Return on 10 year US Treasury Bonds
        self.market_return = market_return # 3yr Return on the SPY (S&P 500 tracker)
        self.mw_url = "" # URL with appended ticker
        self.price_diff = 0
        self.price = 0
        self.df = pd.DataFrame(columns=self.KEYS)
        self.df_filtered = pd.DataFrame(columns=self.KEYS)
        self.data = dict.fromkeys(self.KEYS, 0.0)
        self.filtered_filename = "filtered_dataframe.dat"
        # self.requests = Requests()
        self.ses = requests.session()
        self.terminated = False

    def setTicker(self, ticker):
        self.ticker = ticker

    def getNumRows(self):
        return self.df.shape[0]

    def yahooScrapper(self):
        if self.terminated == False:
            ret = self.yahooSummaryScrapper()
            if ret: # in case of False, then some issue with the Ticker
                self.yahooKeyStatisticsScrapper()
                self.yahooBalanceSheetScrapper()
                self.yahooProfileScrapper()
                self.get_fcf()
                self.calc_wacc()
                self.get_dcf()

                self.calcData()

                # add scrapped data to the Dataframe
                self.addToDb()

    def calcData(self):
        try:
            self.data["NAV"] = (self.data["Total Assets"] - self.data["Intangible Assets"] - self.data["Total Liabilities"]) / self.data["Shares Outstanding"]
            self.data["NAV%"] = self.data["NAV"] / self.data["Previous Close"] - 1

            self.data["NET-NET"] = (self.data["Cash And Cash Equivalents"] + \
                                                0.75 * self.data["Net Receivables"] + \
                                                0.50 * self.data["Inventory"] + \
                                                self.data["Property Plant and Equipment"] - \
                                                self.data["Total Liabilities"]) / self.data["Shares Outstanding"]
            self.data["NET-NET%"] = self.data["NET-NET"] / self.data["Previous Close"] - 1

            self.data["Tangible Book Value"] = self.data["Total Assets"] - self.data["Intangible Assets"] - self.data["Total Liabilities"]
            self.data["Price/Tangible Book Value"] = self.data["Previous Close"] / (self.data["Tangible Book Value"] / self.data["Shares Outstanding"])

            self.data["Cash/sh"] = self.data["Cash And Cash Equivalents"] / self.data["Shares Outstanding"]
            
            # EV > 12
            self.data["EY"] = self.data["EPS (TTM)"] / (self.data["Enterprise Value"] / self.data["Shares Outstanding"])

            # EV/FCF < 10
            self.data["EV/FCF"] = self.data["Enterprise Value"] / self.data["FCF"]

            # self.logger.info("self.data[NAV]: %.2f" % self.data["NAV"])
            # self.logger.info("self.data[NAV%%]: %.2f%%" % self.data["NAV%"])
            # self.logger.info("self.data[NET-NET]: %.2f" % self.data["NET-NET"])
            # self.logger.info("self.data[NET-NET%%]: %.2f%%" % self.data["NET-NET%"])
            # self.logger.info("self.data[EY%%]: %.2f%%" % self.data["EY"])
        except:
            self.logger.error("[calcData] Error calculating data")

    def addToDb(self):
        l_df = pd.DataFrame(self.data, index=[self.next_idx], columns=self.KEYS)
        self.next_idx += 1
        self.df = self.df.append(l_df, sort=False)

    def get_growth_rate(self, trend_list):
        #Calculate the growth rate of a list of line items from 2012 - 2016
        trend_list = [num for num in trend_list if num != 0]
        growth_sum = 0
        for a, b in zip(trend_list[::1], trend_list[1::1]):
            growth_sum += (b - a) / a

        growth_rate = growth_sum/(len(trend_list)-1)
        return growth_rate

    def get_fcf(self):
        cf_generator = self.statement_scraper(self.URLS[2], "Free Cash Flow")
        try:
            cash_flow = next(cf_generator)
            cf_growth_rate = self.get_growth_rate(cash_flow)
            self.data["FCF"] = cash_flow[-1]
            # self.data["CFGR%"] = "{0:.2f}%".format(cf_growth_rate * 100)
            self.data["CFGR%"] = cf_growth_rate * 100
        except:
            self.logger.info("[get_fcf] Error scrapping %s" % self.URLS[2])

    def statement_scraper(self, url, *line_items): 
        statement_url = url.format(self.ticker)
        # r = requests.get(statement_url)
        # soup = bs(r.text, "lxml")
        soup = self.getDataFromXUrl(statement_url)

        for line_item in line_items:
            target_list = []
            try:
                target = soup.find("td", text=line_item).parent
                target_row = target.findAll("td", {"class" : "valueCell"})
                for cell in target_row:
                    num_in_MMs = raw_to_floats(cell.text)
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
                                amount = raw_to_floats(amount.text)
                                _list.append(amount)
                            yield _list

    def getDataFromXUrl(self, url):
        # soup = bs(requests.get(url, verify=True, timeout=None).content, features='html5lib')
        # soup = bs(self.requests.one(url).content, features='html5lib')
        soup = bs(self.ses.get(url, timeout=None).text, features='lxml')
        # soup = bs(requests.get(url, verify=False, timeout=None).content, features='html5lib')
        # soup = bs(urllib2.urlopen(url).read(), features='html5lib')
        return soup

    def getDataFromUrl(self, url):
        # soup = bs(requests.get(url, verify=True, timeout=None).content, features='html5lib')
        # soup = bs(self.requests.one(url).content, features='html5lib')
        soup = bs(self.ses.get(url, timeout=None).content, features='html5lib')
        # soup = bs(requests.get(url, verify=False, timeout=None).content, features='html5lib')
        # soup = bs(urllib2.urlopen(url).read(), features='html5lib')
        return soup

    def yahooProfileScrapper(self):
        try:
            ystock_url = self.URLS[7].format(self.ticker, self.ticker)
            soup = self.getDataFromUrl(ystock_url)        
        except:
            self.logger.info("[yahooProfileScrapper] Error souping %s" % ystock_url)

        try:
            to_scrap = "Sector"
            scraped_data = soup.find(text = to_scrap).find_next().text
            self.data[to_scrap] = scraped_data

            to_scrap = "Industry"
            scraped_data = soup.find(text = to_scrap).find_next().text
            self.data[to_scrap] = scraped_data
        except:
            self.logger.info("[yahooProfileScrapper] Error scraping %s" % to_scrap)

    def yahooSummaryScrapper(self):
        MAX_RETRIES = 5
        success = False

        try:
            ystock_url = self.URLS[6].format(self.ticker, self.ticker)
            soup = self.getDataFromUrl(ystock_url)
        except:
            self.logger.info("[yahooSummaryScrapper] Error souping %s" % ystock_url)

        try:
            self.data["Ticker"] = self.ticker
            
            done = False
            retries = 0
            while retries < MAX_RETRIES:
                try:
                    to_scrap = "Volume"
                    scraped_data = soup.find(text = to_scrap).find_next().text
                    self.data[to_scrap] = raw_to_num(scraped_data)
                    success = True
                    break
                except:
                    self.logger.error("[yahooSummaryScrapper] Retrying scrapping of Volume")
                    soup = self.getDataFromUrl(ystock_url)
                    retries = retries + 1
            if success == False:
                return False

            to_scrap = "Previous Close"
            scraped_data = soup.find(text = to_scrap).find_next().text
            self.data[to_scrap] = raw_to_num(scraped_data)

            to_scrap = "Market Cap"
            scraped_data = soup.find(text = to_scrap).find_next().text
            self.data[to_scrap] = raw_to_floats(scraped_data)

            to_scrap = "PE Ratio (TTM)"
            scraped_data = soup.find(text = to_scrap).find_next().text
            self.data[to_scrap] = raw_to_num(scraped_data)

            to_scrap = "EPS (TTM)"
            scraped_data = soup.find(text = to_scrap).find_next().text
            self.data[to_scrap] = raw_to_num(scraped_data)

            # Forward Dividend & Yield
            to_scrap = "Forward Dividend & Yield"
            scraped_data = soup.find(text = to_scrap).find_next().text
            scraped_data = scraped_data.split(' ')
            self.data["Dividend"] = raw_to_num(scraped_data[0])
            self.data["Dividend %"] = raw_to_num(scraped_data[1].split('(')[1].split(')')[0].split('%')[0])

            return True
        except:
            self.logger.info("[yahooSummaryScrapper] Error scraping %s" % to_scrap)

    def yahooKeyStatisticsScrapper(self):
        try:
            ystock_url = self.URLS[3].format(self.ticker)
            soup = self.getDataFromUrl(ystock_url)
            # soup = bs(requests.get(ystock_url).content, features='html5lib')
        except:
            self.logger.info("[yahooKeyStatisticsScrapper] Error souping %s" % ystock_url)

        try:
            # Total Debt
            to_scrap = "Total Debt"
            scraped_data = soup.find(text = to_scrap).find_next(class_='Fz(s) Fw(500) Ta(end)').text
            self.data[to_scrap] = raw_to_floats(scraped_data)
            
            # Enterprise Value
            to_scrap = "Enterprise Value"
            scraped_data = soup.find(text = to_scrap).find_next().find_next().text
            self.data[to_scrap] = raw_to_floats(scraped_data)

            # Shares Outstanding
            to_scrap = "Shares Outstanding"
            scraped_data = soup.find(text = to_scrap).find_next(class_='Fz(s) Fw(500) Ta(end)').text
            self.data[to_scrap] = raw_to_floats(scraped_data)
            
            # Price/Sales < 1
            to_scrap = "Price/Sales"
            scraped_data = soup.find(text = to_scrap).find_next(class_='Fz(s) Fw(500) Ta(end)').text
            self.data[to_scrap] = raw_to_num(scraped_data)

            # Beta
            to_scrap = "Beta (3y)"
            scraped_data = soup.find(text = to_scrap).find_next(class_='Fz(s) Fw(500) Ta(end)').text
            self.beta = float(scraped_data) 
            self.data[to_scrap] = self.beta
        except:
            self.logger.info("[yahooKeyStatisticsScrapper] Error scraping %s" % to_scrap)

        try:
            self.cost_of_eq = self.risk_free_rate + self.beta * (self.market_return - self.risk_free_rate)
        except:
            self.logger.info("[yahooKeyStatisticsScrapper] Error in cost_of_eq calc")

    def yahooBalanceSheetScrapper(self):
        try:
            ystock_url = self.URLS[5].format(self.ticker)
            soup = self.getDataFromUrl(ystock_url)
            # soup = bs(requests.get(ystock_url).content, features='html5lib')
        except:
            self.logger.info("[yahooBalanceSheetScrapper] Error souping %s" % ystock_url)

        try:            
            # Cash And Cash Equivalents
            to_scrap = "Cash And Cash Equivalents"
            scraped_data = soup.find(text = to_scrap).find_next(class_='Fz(s) Ta(end) Pstart(10px)').text            
            self.data[to_scrap] = raw_to_num(scraped_data, multiplier=1000)

            # Net Receivables
            to_scrap = "Net Receivables"
            scraped_data = soup.find(text = to_scrap).find_next(class_='Fz(s) Ta(end) Pstart(10px)').text            
            self.data[to_scrap] = raw_to_num(scraped_data, multiplier=1000)

            # Inventory
            to_scrap = "Inventory"
            scraped_data = soup.find(text = to_scrap).find_next(class_='Fz(s) Ta(end) Pstart(10px)').text
            self.data[to_scrap] = raw_to_num(scraped_data, multiplier=1000)

            # Intangible Assets
            to_scrap = "Intangible Assets"
            scraped_data = soup.find(text = to_scrap).find_next(class_='Fz(s) Ta(end) Pstart(10px)').text
            self.data[to_scrap] = raw_to_num(scraped_data, multiplier=1000)

            # Property Plant and Equipment
            to_scrap = "Property Plant and Equipment"
            scraped_data = soup.find(text = to_scrap).find_next(class_='Fz(s) Ta(end) Pstart(10px)').text
            self.data[to_scrap] = raw_to_num(scraped_data, multiplier=1000)

            # Below are values that are bold in the data table
            # Total Liabilities
            to_scrap = "Total Liabilities"                                         
            scraped_data = soup.find(text = to_scrap).find_next(class_='Fw(b) Fz(s) Ta(end) Pb(20px)').text
            self.data[to_scrap] = raw_to_num(scraped_data, multiplier=1000)

            # Total Assets
            to_scrap = "Total Assets"
            scraped_data = soup.find(text = to_scrap).find_next(class_='Fw(b) Fz(s) Ta(end) Pb(20px)').text
            self.data[to_scrap] = raw_to_num(scraped_data, multiplier=1000)
        except:
            self.logger.info("[yahooBalanceSheetScrapper] Error scraping %s" % to_scrap)
        
    def print_data(self):
        # print("The Weighted Average Cost of Capital for {0:s} is {1:.2f}%. Other key stats are listed below (Total Debt and Market Cap in MM's)\n\n".format(self.ticker, (self.wacc* 100)))
        print self.df
        # for key in self.SUMMARY_DATA:
        #     print("{} : {}".format(key, self.data[key]))
    
    def print_calcs(self):
        print("{} : {}".format("PV", self.PV))
        print("{} : {}".format("Price-per-Share", self.price_per_share))
        print("{} : {}%".format("Price-Diff", self.price_diff))

    def df_to_csv(self, action):
        filename = "%s.csv" % action
        self.terminated = True
        self.df.to_csv(filename, encoding='utf-8', index=False)
        self.logger.info("[df_to_csv] Dataframe saved to file %s" % filename)

    def csv_to_df(self, action):
        filename = "%s.csv" % action
        if os.path.isfile(filename):
            self.df = pd.read_csv(filename, names=self.KEYS, header=0)
            return 1
        else:
            self.logger.error("[csv_to_df] file %s does not exist!" % filename)
            return None

    def get_dcf(self):
        try:
            wacc = self.data["WACC%"] / 100 # transform to float
            growth_rate = self.data["CFGR%"] / 100 # transform to float
            self.cf_list = []
            self.discounted_cf_list = []
            CF0 = self.data["FCF"]

            for i in range(1, 6):
                cf = CF0 * (1.05 ** i)
                discounted = cf / ((1 + wacc) ** i)
                self.cf_list.append(cf)
                self.discounted_cf_list.append(discounted)
          
            # TCF = (cf_list[-1] * wacc^5)/ (wacc - growth_rate)
            # TCF = (cf_list[-1] * wacc**5)/ (wacc - growth_rate)
            self.TCF = self.cf_list[-1] / (wacc - growth_rate)
            self.discounted_cf_list.append(self.TCF / ((1 + wacc) ** i))
            self.PV = sum(self.discounted_cf_list)
            self.price_per_share = self.PV / self.data["Shares Outstanding"]
            rate = self.price_per_share / self.data["Previous Close"]
            self.price_diff = (rate - 1) * 100
        except:
            self.logger.error("[get_dcf] ERROR !")

    def calc_wacc(self):
        # requires to be executed after self.yahooKeyStatisticsScrapper
        # requires to be executed after self.yahooSummaryScrapper
        is_generator = self.statement_scraper(self.URLS[1], "Gross Interest Expense", "Income Tax", "Pretax Income") # income statement generator
        # import pdb; pdb.set_trace()
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

            self.cost_of_debt = int_expense/self.data["Total Debt"]

            weighted_coe = (float(self.data["Market Cap"])/(float(self.data["Total Debt"]) + float(self.data["Market Cap"]))) * self.cost_of_eq
            weighted_cod = (float(self.data["Total Debt"])/(float(self.data["Market Cap"]) + float(self.data["Total Debt"]))) * self.cost_of_debt * (1 - tax_rate)

            wacc = weighted_coe + weighted_cod 
            # self.data["WACC"] = "{0:.2f}%".format(wacc * 100)
            self.data["WACC%"] = wacc * 100
        except:
            self.logger.error("[calc_wacc] error in function")