import requests
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/102.0.0.0 Safari/537.36'
}


def get_id(isin):
    # query = re.sub(r'[^a-zA-Z0-9 ]', '', yf.Ticker(symbol).info['longName'])
    resp = requests.get(f'https://www.ls-tc.de/_rpc/json/.lstc/instrument/search/main?q={isin}', headers=headers)
    assert resp.status_code == 200, resp.status_code
    return resp.json()[0]['id'], resp.json()[0]['displayname']


def get_history(isin):
    id, name = get_id(isin)
    url = f'https://www.ls-tc.de/_rpc/json/instrument/chart/dataForInstrument?instrumentId={id}' #&marketId=1&quotetype=mid&series=history&localeId=2'
    resp = requests.get(url, headers=headers)
    assert resp.status_code == 200, resp.status_code

    # dfhistory = pd.DataFrame(resp.json()['series']['history']['data'], columns=['Date', 'Price'])
    # dfhistory.Date *= 1000000
    # dfhistory.Date = pd.to_datetime(dfhistory.Date)
    # dfhistory.set_index('Date', inplace=True)

    # dfintraday = pd.DataFrame(resp.json()['series']['intraday']['data'], columns=['Date', 'Price'])
    # dfintraday.Date *= 1000000
    # dfintraday.Date = pd.to_datetime(dfintraday.Date)
    # dfintraday.set_index('Date', inplace=True)
    # print(dfintraday)
    # resp.json()['series']['intraday']['data'][-1]
    return name, resp.json()['series']['intraday']['data']
    # return name, dfintraday.to_json(orient='records') #dfhistory.to_json(orient='records'),

# def get_symbol_for_isin(isin, user=None):
#     # First check if user provided symbol
#     if user:
#         user_symbol = UserProvidedSymbol.objects.filter(user=user, isin=isin).first()
#         if user_symbol:
#             return {
#                 "symbol": user_symbol.symbol,
#                 "name": user_symbol.name,
#                 "source": "user"
#             }

#     # Then try Yahoo Finance API
#     url = 'https://query1.finance.yahoo.com/v1/finance/search'
#     params = dict(
#         q=isin,
#         quotesCount=1,
#         newsCount=0,
#         listsCount=0,
#         quotesQueryId='tss_match_phrase_query'
#     )

#     resp = requests.get(url=url, headers=headers, params=params)
#     data = resp.json()
#     if 'quotes' in data and len(data['quotes']) > 0:
#         return {
#             "symbol": data['quotes'][0]['symbol'],
#             "name": data['quotes'][0]['longname'] if 'longname' in data['quotes'][0] else data['quotes'][0]['shortname'],
#             "source": "api"
#         }
#     elif user:
#         return {
#             "symbol": "Not found",
#             "name": "Not found",
#             "not_found": True,
#             "source": "none"
#         }
    
#     return None

