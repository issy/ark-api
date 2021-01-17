import requests
import bs4
from bs4 import BeautifulSoup as soup
from typing import List, Union
from pymongo import MongoClient
import config


headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.141 Safari/537.36'
}


client = MongoClient(config.MONGO_CONNECTION_STRING)
db = client[config.MONGO_DB]
coll = db.intel


class SearchResult:
    def __init__(self, result):
        self.title = result.find(
            "h4", {"class": "result-title"}).find("a").contents[0].strip()
        url = result.find(
            'h4', {'class': 'result-title'}).find('a').get('href')
        self.url = f"https://ark.intel.com{url}"


class CPUPage:
    def __init__(self, page: soup):
        specs_table = page.find('table', {'class': 'specs-section'})
        self.__dict__ = self.parse_table(specs_table)

    def parse_table(self, table):

        def evaluate(item):
            if isinstance(item, bs4.element.Tag):
                return f"https://ark.intel.com{item['href']}"
            item = item.strip()
            if item.lower() in ('yes', 'no'):
                return {'yes': True, 'no': False}[item.lower()]
            if item.isdigit():
                return int(item)
            return item

        return {
            span['data-key']: evaluate([
                i for i in span.contents if i not in ('', '\n', ' ')][0])
            for span in table.find_all('span', {'class': 'value'})
            if 'data-key' in span.attrs
        }


class ProductFamilyPage:
    pass


class SearchResultsPage:
    pass


class NoResultsPage:
    pass


def get_page_type(page: soup) -> type:
    if page.find('h2', text='No products matching your request were found.'):
        return NoResultsPage
    elif page.find('h1', text='Page not found'):
        return NoResultsPage
    elif page.find('table', {'id': 'product-table'}):
        return ProductFamilyPage
    elif page.find('div', {'class': 'search-results'}):
        return SearchResultsPage
    elif page.find('div', {'class': 'specs-section'}):
        return CPUPage


def parse_results(page: soup) -> List[str]:
    results = [SearchResult(result) for result in page.find_all(
        'div', {'class': 'search-result'})]
    filtered_results_urls = []
    for result in results:
        for banned_word in ('nuc', 'fpga', 'generation', 'ethernet', 'wireless', 'products formerly', 'heat sink'):
            if banned_word not in result.title.lower().split():
                filtered_results_urls.append(result.url)
    for url in filtered_results_urls:
        page = soup(requests.get(url, headers=headers).text, 'html.parser')
        page_type = get_page_type(page)


def sanitise(document: dict) -> dict:
    return {
        'name': document.get('ProcessorNumber'),
        'base_clock': document.get('ClockSpeed'),
        'boost_clock': document.get('ClockSpeedMax', document.get('ClockSpeed')),
        'hyperthreading': document.get('HyperThreading', False),
        'tdp': int(document.get('MaxTDP').lower().strip('w').strip()),
        'sockets': document.get('SocketsSupported'),
        'vtd': document.get('VTD', False),
        'aes': document.get('AESTech', False),
        'url': document.get('url'),
        'vpro': document.get('VProTechnology'),
        'max_mem': document.get('MaxMem'),
        'pcie_lanes': document.get('NumPCIExpressPorts'),
        'ecc': document.get('ECCMemory', False)
    }


def upload(results: List[dict]):
    for item in results:
        doc_exists = coll.find({"name": item['ProcessorNumber']})
        if doc_exists:
            continue
        coll.insert_one(sanitise(item))


def search(search_string: str) -> List[dict]:
    url = f"https://ark.intel.com/content/www/us/en/ark/search.html?_charset_=UTF-8&q={search_string}"
    r = requests.get(url, headers=headers)
    page = soup(r.text, 'html.parser')
    page_type = get_page_type(page)
    if page_type is NoResultsPage:
        return []
    elif page_type in (SearchResultsPage, ProductFamilyPage):
        results = page_type(page)
        upload(results)
