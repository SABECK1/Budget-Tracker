import requests
import aiohttp
import asyncio
from typing import Optional, Tuple, List, Dict

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


# Async versions for concurrent fetching
async def get_id_async(isin: str, session: aiohttp.ClientSession) -> Tuple[Optional[str], Optional[str]]:
    """Async version of get_id"""
    try:
        url = f'https://www.ls-tc.de/_rpc/json/.lstc/instrument/search/main?q={isin}'
        async with session.get(url, headers=headers) as resp:
            if resp.status != 200:
                return None, None
            data = await resp.json()
            if data and len(data) > 0:
                return data[0]['id'], data[0]['displayname']
            return None, None
    except Exception as e:
        print(f"Error fetching ID for {isin}: {e}")
        return None, None


async def get_history_async(isin: str, session: aiohttp.ClientSession) -> Tuple[str, List]:
    """Async version of get_history"""
    try:
        id, name = await get_id_async(isin, session)
        if not id or not name:
            return f"Unknown ({isin})", []  # fallback

        url = f'https://www.ls-tc.de/_rpc/json/instrument/chart/dataForInstrument?instrumentId={id}'
        async with session.get(url, headers=headers) as resp:
            if resp.status != 200:
                return f"Unknown ({isin})", []
            data = await resp.json()

        intraday_data = data.get('series', {}).get('intraday', {}).get('data', [])
        plotline_preday = data.get("info", {}).get("plotlines", [{}])[0].get("value")
        return name, intraday_data, plotline_preday
    except Exception as e:
        print(f"Error fetching price for {isin}: {e}")
        return f"Error ({isin})", []

async def fetch_single_price(isin: str, max_concurrent: int) -> Dict[str, any]:
    semaphore = asyncio.Semaphore(max_concurrent)
    async with semaphore:
        async with aiohttp.ClientSession() as session:
            try:
                name, intraday_data, preday = await get_history_async(isin, session)
                if intraday_data and len(intraday_data) > 0:
                    current_price = float(intraday_data[-1][1])
                    success = True
                else:
                    current_price = None
                    success = False
                return {
                    'isin': isin,
                    'name': name,
                    'current_price': current_price,
                    'success': success,
                    'intraday_data': intraday_data,
                    'preday': preday
                }
            except Exception as e:
                print(f"Failed to fetch data for {isin}: {e}")
                return {
                    'isin': isin,
                    'name': f"Error ({isin})",
                    'current_price': None,
                    'success': False,
                    'intraday_data': [],
                    'preday': []
                }


async def fetch_multiple_prices(isins: List[str], max_concurrent: int = 5) -> Dict[str, Dict[str, any]]:
    """Fetch price data for multiple ISINs concurrently with rate limiting"""
    # Create tasks for all ISINs
    tasks = [fetch_single_price(isin, max_concurrent) for isin in isins]

    # Execute all tasks concurrently
    results = await asyncio.gather(*tasks, return_exceptions=True)

    # Convert to dictionary keyed by ISIN
    price_dict = {}
    for result in results:
        if isinstance(result, Exception):
            print(f"One of the tasks failed with exception: {result}")
        else:
            price_dict[result['isin']] = result
    return price_dict

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
