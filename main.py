#!/usr/bin/env python

# from auth import consumer_key, consumer_secret, access_token, access_token_secret, api_key 
import auth
import os
import csv
import re
import sys
import requests
import logging
import time
import signal
import warnings
# sys.path.insert(0, '/Users/tamirgz/Documents/PythonProjects/Finance/Stocksheet/modules')
from fundamentals import Fundamentals

warnings.simplefilter(action='ignore', category=FutureWarning)

DEFAULT_THS = 50 # percent
URL = "https://www.finviz.com/quote.ashx?t={}"

logger = None
fundas = None
terminated = False
action = ""

# to_analyze = []

def exit_gracefully(signum, frame):
    global fundas, terminated, logger, action
    # restore the original signal handler as otherwise evil things will happen
    # in raw_input when CTRL+C is pressed, and our signal handler is not re-entrant
    signal.signal(signal.SIGINT, original_sigint)

    try:
        if raw_input("\nReally quit? (y/n)> ").lower().startswith('y'):
            fundas.df_to_csv(action)
            terminated = True
            sys.exit(1)

    except KeyboardInterrupt:
        print("Ok ok, quitting")
        sys.exit(1)

    # restore the exit gracefully handler here    
    signal.signal(signal.SIGINT, exit_gracefully)

def update_last_analyzed(filename, idx):
    with open(filename,"w+") as f:
        f.write(str(idx))

def analyze_ticker(ticker, ongoing_print=True):
    global fundas, terminated, logger, action
    # response = requests.get(URL.format(ticker))
    # if response.status_code == 200:
    try:
        fundas.setTicker(ticker)
        # fundas.calc_wacc()
        fundas.yahooScrapper()
        if ongoing_print:
            fundas.print_data()
        # warren.get_cf()   
        # warren.get_dcf()
        # if ongoing_print:
            # warren.print_calcs()
        # if warren.price_diff >= DEFAULT_THS:
            # to_analyze.append(ticker)
            # with open("candidates.dat", "a+") as f:
                # f.write("%s (%f, %f, %f, %f, %s, %f)\n" % 
                    # (ticker, warren.price_diff, warren.price, warren.price_per_share, self.wacc, str(warren.cf_list[0]), self.TCF, str(warren.discounted_cf_list[0])))
    except ZeroDivisionError:
        print("Unable to calculate cost of debt for this stock")
    # else:
    #     print("Ticker not found, check spelling and try again")

def get_start_index(l_action):
    global fundas, terminated, logger, action

    ret = fundas.csv_to_df(l_action)
    idx = 0
    if ret == 1: # success
        idx = fundas.getNumRows()
    return idx

def main():
    global fundas, terminated, logger, action
    ticker_list = []
    save_to_csv = False

    if len(sys.argv) <= 1:
        print("Not enough parameters")
    else:
        action = sys.argv[1]
        
        filename = "%s.dat" % action
        if action == "ALL":
            idx = get_start_index(action)
            file1 = open('tickers/nasdaqlisted.txt')
            file2 = open('tickers/otherlisted.txt')
            for line in file1.readlines()[1:] + file2.readlines()[1:]:
                stock = line.strip().split('|')[0]
                if (re.match(r'^[A-Z]+$',stock)):
                    ticker_list.append(stock)
            file1.close()
            file2.close()

            ticker_list_len = len(ticker_list)

            while idx < ticker_list_len and terminated == False:
                start = time.time()
                ticker = ticker_list[idx]
                analyze_ticker(ticker, ongoing_print=False)
                idx = idx + 1
                end = time.time()
                print "[%s]========================\t%s\t[%d / %d : %f] ========================" % (action, ticker, idx, len(ticker_list), end-start)
            save_to_csv = True
        elif action == "NASDAQ":
            idx = get_start_index(action)
            file1 = open('tickers/nasdaqlisted.txt')
            for line in file1.readlines()[1:]:
                stock = line.strip().split('|')[0]
                if (re.match(r'^[A-Z]+$',stock)):
                    ticker_list.append(stock)
            file1.close()

            ticker_list_len = len(ticker_list)

            while idx < ticker_list_len and terminated == False:
                start = time.time()
                ticker = ticker_list[idx]
                analyze_ticker(ticker, ongoing_print=False)
                idx = idx + 1
                end = time.time()
                print "[%s]========================\t%s\t[%d / %d : %f] ========================" % (action, ticker, idx, len(ticker_list), end-start)
            save_to_csv = True
        elif action == "OTHER":
            idx = get_start_index(action)
            file2 = open('tickers/otherlisted.txt')
            for line in file2.readlines()[1:]:
                stock = line.strip().split('|')[0]
                if (re.match(r'^[A-Z]+$',stock)):
                    ticker_list.append(stock)
            file2.close()

            ticker_list_len = len(ticker_list)

            while idx < ticker_list_len and terminated == False:
                start = time.time()
                ticker = ticker_list[idx]
                analyze_ticker(ticker, ongoing_print=False)
                idx = idx + 1
                end = time.time()
                print "[%s]========================\t%s\t[%d / %d : %f] ========================" % (action, ticker, idx, len(ticker_list), end-start)
            save_to_csv = True
        else:
            ticker = sys.argv[1]
            # print "======================== %s ========================" % ticker
            start = time.time()
            analyze_ticker(ticker)
            end = time.time()
            logger.info("Time Elapsed: %f" % (end - start))

    if save_to_csv:
        fundas.df_to_csv(action)
        
    # print "Potential stocks:\n"
    # print to_analyze
    # ticker = raw_input("Enter the ticker you would like to search for: ")
    # if response.status_code == 200:
    # # if ticker in ticker_list:
    #   try:
    #       warren = Warren_Buffet(0.025, 0.09, ticker)
    #       warren.calc_wacc()
    #       warren.get_cf() 
    #       warren.print_data() 
    #       warren.get_dcf()
    #       warren.print_calcs()
    #   except ZeroDivisionError:
    #       print("Unable to calculate cost of debt for this stock")
    #   # with open("Stocksheet.csv", "w") as sfile:
    #   #   writer = csv.writer(sfile)
    #   #   writer.writerow(["Ticker", ticker])
    #   #   for key, value in warren.SUMMARY_DATA.items():
    #   #       writer.writerow([key, value])
    #   # sfile.close()
    # else:
    #   print("Ticker not found, check spelling and try again")

if __name__ == "__main__":
    # Initialize Logging
    logger = logging.getLogger()
    handler = logging.StreamHandler()
    formatter = logging.Formatter(
            '%(asctime)s %(name)-12s %(levelname)-8s %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)

    fundas = Fundamentals(0.025, 0.09, logger)

    # store the original SIGINT handler
    original_sigint = signal.getsignal(signal.SIGINT)
    signal.signal(signal.SIGINT, exit_gracefully)
    main()
