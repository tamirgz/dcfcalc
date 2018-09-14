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