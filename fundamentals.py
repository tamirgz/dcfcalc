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
            "Enterprise Value", \
            "Total Debt", \
            "Net Receivables", \
            "Inventory", \
            "Property Plant and Equipment", \
            "Total Assets", \
            "Intangible Assets", \
            "Total Liabilities", \
            "Shares Outstanding", \
            "Beta", \
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
            "EV/FCF"]

    def __init__(self, risk_free_rate, market_return, logger):
        self.name = "Fundamentals"
        self.logger = logger
        self.risk_free_rate = risk_free_rate # Return on 10 year US Treasury Bonds
        self.market_return = market_return # 3yr Return on the SPY (S&P 500 tracker)
        self.mw_url = "" # URL with appended ticker
        self.wacc = 0
        self.growth_rate = 0
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
            self.yahooSummaryScrapper()
            self.yahooKeyStatisticsScrapper()
            self.yahooBalanceSheetScrapper()
            self.get_cf()

            # add scrapped data to the Dataframe
            self.addToDb()

            self.calcData()

    def calcData(self):
        self.data["NAV"] = (self.data["Total Assets"] - self.data["Intangible Assets"] - self.data["Total Liabilities"]) / self.data["Shares Outstanding"]
        self.data["NAV%"] = self.data["NAV"] / self.data["Previous Close"] - 1

        self.data["NET-NET"] = (self.data["Cash And Cash Equivalents"] + \
                                            0.75 * self.data["Net Receivables"] + \
                                            0.50 * self.data["Inventory"] + \
                                            self.data["Property Plant and Equipment"] - \
                                            self.data["Total Liabilities"]) / self.data["Shares Outstanding"]
        self.data["NET-NET%"] = self.data["NET-NET"] / self.data["Previous Close"] - 1
        
        # EV > 12
        self.data["EY"] = self.data["EPS (TTM)"] / (self.data["Enterprise Value"] / self.data["Shares Outstanding"])

        # EV/FCF < 10
        self.data["EV/FCF"] = self.data["Enterprise Value"] / self.data["FCF"]

        # self.logger.info("self.data[NAV]: %.2f" % self.data["NAV"])
        # self.logger.info("self.data[NAV%%]: %.2f%%" % self.data["NAV%"])
        # self.logger.info("self.data[NET-NET]: %.2f" % self.data["NET-NET"])
        # self.logger.info("self.data[NET-NET%%]: %.2f%%" % self.data["NET-NET%"])
        # self.logger.info("self.data[EY%%]: %.2f%%" % self.data["EY"])

    def addToDb(self):
        l_df = pd.DataFrame(self.data, index=[self.next_idx], columns=self.KEYS)
        self.next_idx += 1
        self.df = self.df.append(l_df, sort=False)

    def get_cf(self):
        cf_generator = self.statement_scraper(self.URLS[2], "Free Cash Flow")
        try:
            cash_flow = next(cf_generator)
            self.data["FCF"] = cash_flow[-1]
        except:
            self.logger.info("[get_cf] Error scrapping %s" % self.URLS[2])

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


    def getDataFromUrl(self, url):
        # soup = bs(requests.get(url, verify=True, timeout=None).content, features='html5lib')
        # soup = bs(self.requests.one(url).content, features='html5lib')
        soup = bs(self.ses.get(url, timeout=None).content, features='html5lib')
        # soup = bs(requests.get(url, verify=False, timeout=None).content, features='html5lib')
        # soup = bs(urllib2.urlopen(url).read(), features='html5lib')
        return soup

    def yahooSummaryScrapper(self):
        try:
            ystock_url = self.URLS[6].format(self.ticker, self.ticker)
            soup = self.getDataFromUrl(ystock_url)
        except:
            self.logger.info("[yahooSummaryScrapper] Error souping %s" % ystock_url)

        try:
            self.data["Ticker"] = self.ticker
            
            to_scrap = "Volume"
            scraped_data = soup.find(text = to_scrap).find_next().text
            self.data[to_scrap] = raw_to_num(scraped_data)

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
            to_scrap = "Beta"
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