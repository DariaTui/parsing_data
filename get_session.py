import requests
from bs4 import BeautifulSoup
import json


def set_cookies():
    s = requests.Session()

    start_r = s.get('https://101hotels.com/')
    if start_r.status_code == 200:
        print(f'Код: {start_r.status_code}. Куки устанавливаются...')

    cookies = ''
    for k, v in start_r.cookies.items():
        cookies+=f'{k}={v}; '

    headers = {'Accept-Language':'ru,en-US;q=0.9,en;q=0.8',
               'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 YaBrowser/24.4.0.0 Safari/537.36',
               'Cookie':cookies[:-2]
              }
    s.headers = headers
    return s

session = set_cookies()

