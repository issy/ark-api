import requests
from bs4 import BeautifulSoup
import config
import json
import utils


with open('queries.json', 'r') as f:
    queries = json.loads(f.read())

for query in queries:
    results = utils.search(query)
    if not results:
        continue
    utils.upload(results)
