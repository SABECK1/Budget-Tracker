import requests
import pandas as pd
import re
import yfinance as yf

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/102.0.0.0 Safari/537.36'
}


def get_id(symbol):
    query = re.sub(r'[^a-zA-Z0-9 ]', '', yf.Ticker(symbol).info['longName'])
    resp = requests.get(f'https://www.ls-tc.de/_rpc/json/.lstc/instrument/search/main?q={query}&localeId=2', headers=headers)
    assert resp.status_code == 200, resp.status_code
    return resp.json()[0]['id']


def get_history(symbol):
    id = get_id(symbol)
    url = f'https://www.ls-tc.de/_rpc/json/instrument/chart/dataForInstrument?instrumentId={id}&marketId=1&quotetype=mid&series=history&localeId=2'
    resp = requests.get(url, headers=headers)
    assert resp.status_code == 200, resp.status_code
    df = pd.DataFrame(resp.json()['series']['history']['data'], columns=['Date', 'Price'])
    df.Date *= 1000000
    df.Date = pd.to_datetime(df.Date)
    df.set_index('Date', inplace=True)
    return df

def get_symbol_for_isin(isin):
    url = 'https://query1.finance.yahoo.com/v1/finance/search'

    params = dict(
        q=isin,
        quotesCount=1,
        newsCount=0,
        listsCount=0,
        quotesQueryId='tss_match_phrase_query'
    )

    resp = requests.get(url=url, headers=headers, params=params)
    data = resp.json()
    if 'quotes' in data and len(data['quotes']) > 0:
        return data['quotes'][0]['symbol']
    else:
        return None

print(get_symbol_for_isin('AU000000DRO2'))