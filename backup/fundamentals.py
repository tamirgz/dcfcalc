import pandas as pd
from bs4 import BeautifulSoup as bs
import requests
import sys

headers = {}
headers['User-Agent'] = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/67.0.3396.99 Safari/537.36'
metric = ['Market Cap', 'P/E', 'EPS (ttm)', 'Dividend', 'Dividend %', 'Beta']

def get_fundamental_data(df):
    for symbol in df.index:
        try:
            url = ("http://finviz.com/quote.ashx?t=" + symbol.lower())
            soup = bs(requests.get(url).content, features='html5lib') 
            for m in df.columns:
                df.loc[symbol,m] = fundamental_metric(soup,m)
        except Exception as e:
            print (symbol, 'not found')
    return df

def fundamental_metric(soup, metric):
    return soup.find(text = metric).find_next(class_='snapshot-td2').text

def main():
    if len(sys.argv) > 1:
        stock_list = sys.argv[1]
    else:
        stock_list = ['AAPL']
    
    df = pd.DataFrame(index=stock_list,columns=metric)
    df = get_fundamental_data(df)
    print df

if __name__ == "__main__":
    main()

