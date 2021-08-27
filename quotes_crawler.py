import json
import time
import requests
from bs4 import BeautifulSoup 


start_id = 101
while start_id <= 100:
    quotes = []
    url = f"https://www.goodreads.com/quotes/tag/inspirational?page={start_id}"
    r = requests.get(url)
    soup = BeautifulSoup(r.content, 'html5lib') 
    for row in soup.findAll('div', attrs = {'class':'quote mediumText'}): 
        quote_author = row.find('div', attrs={'class': "quoteDetails"}).find('div', attrs={'class': "quoteText"}).text.split('―')
        
        quote = quote_author[0].strip()
        author = quote_author[1].strip().split('\n')[0].strip()
        
        quote_dict = {
            "quote": quote,
            "author": author if not author.endswith(',') else author[:-1].strip(),
        }
        print(quote_dict)
        quotes.append(quote_dict)

    with open(f'quotes/{start_id}.json', 'w+') as f:
        json.dump(quotes, f)

    start_id += 1
    time.sleep(2)

def isEnglish(s):
    try:
        s.encode(encoding='utf-8').decode('ascii')
    except UnicodeDecodeError:
        return False
    else:
        return True

clean_id = 1
while clean_id <= 100:
    with open(f'quotes/{clean_id}.json') as f:
        data = json.load(f)

    new_data = []
    for d in data:
        if isEnglish(d['quote'].replace('“', '').replace('”', '').replace('’', '')):
            if len(d['quote']) <= 202:
                new_data.append(d)

    with open(f'quotes/{clean_id}.json', 'w+') as f:
        json.dump(new_data, f)
    
    clean_id += 1
