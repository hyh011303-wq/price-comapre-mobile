import requests
from bs4 import BeautifulSoup
import random
import time

from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from urllib.parse import urljoin

class PriceScraper:
    def __init__(self):
        self.headers_list = [
            {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'},
            {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, fee Gecko) Version/14.1.1 Safari/605.1.15'},
            {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0'}
        ]
        
        # Configure session with retries
        self.session = requests.Session()
        retries = Retry(total=3, backoff_factor=1, status_forcelist=[500, 502, 503, 504])
        adapter = HTTPAdapter(max_retries=retries)
        self.session.mount('http://', adapter)
        self.session.mount('https://', adapter)

    def get_random_headers(self):
        return random.choice(self.headers_list)

    def scrape_site(self, site_config, keyword):
        url = site_config['url_pattern'].format(keyword)
        try:
            response = self.session.get(url, headers=self.get_random_headers(), timeout=10)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')
            
            title_element = soup.select_one(site_config['title_selector'])
            price_selector = site_config['price_selector']
            price_text = ""
            
            if "::attr(" in price_selector:
                parts = price_selector.split("::attr(")
                css_selector = parts[0].strip()
                attr_name = parts[1].rstrip(")")
                if css_selector:
                    price_element = soup.select_one(css_selector)
                    if price_element:
                        price_text = price_element.get(attr_name, "")
            else:
                price_element = soup.select_one(price_selector)
                if price_element:
                    price_text = price_element.get_text(strip=True)
            
            if title_element and price_text:
                title = title_element.get_text(strip=True)
                price = self._parse_price(price_text)
                product_url = url
                link_el = None
                if title_element.name == 'a':
                    link_el = title_element
                else:
                    link_el = title_element.find_parent('a') or title_element.find('a')
                if link_el and link_el.get('href'):
                    product_url = urljoin(url, link_el.get('href'))
                
                return {
                    'site_name': site_config['name'],
                    'product_title': title,
                    'price': price,
                    'price_text': price_text,
                    'url': product_url,
                    'success': True
                }
            else:
                return {
                    'site_name': site_config['name'],
                    'error': 'Elements not found',
                    'success': False
                }
        except Exception as e:
            return {
                'site_name': site_config['name'],
                'error': str(e),
                'success': False
            }

    def _parse_price(self, price_str):
        clean_str = ''.join(c for c in price_str if c.isdigit())
        try:
            return float(clean_str)
        except ValueError:
            return 0.0
