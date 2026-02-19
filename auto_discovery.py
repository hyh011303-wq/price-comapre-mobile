import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse

class SiteAnalyzer:
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept-Language': 'ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
        }
        self.session = requests.Session()

    def analyze(self, base_url):
        if not base_url.startswith("http"):
            base_url = "https://" + base_url
        domain = urlparse(base_url).netloc
        site_name = domain.replace('www.', '').split('.')[0]
        try:
            search_pattern = self._find_search_pattern(base_url)
            if not search_pattern:
                search_pattern = self._guess_platform_search_pattern(base_url)
            if not search_pattern:
                return {'success': False, 'message': '검색 패턴 찾기 실패', 'site_name': site_name}

            test_keywords = ["측기", "현장"]
            best_selectors = {'title': '', 'price': ''}
            for kw in test_keywords:
                test_url = search_pattern.format(kw)
                try:
                    resp = self.session.get(test_url, headers=self.headers, timeout=10)
                    if resp.status_code == 200:
                        soup = BeautifulSoup(resp.text, 'html.parser')
                        selectors = self._detect_selectors(soup)
                        if not best_selectors['title'] and selectors.get('title'):
                            best_selectors['title'] = selectors['title']
                        if not best_selectors['price'] and selectors.get('price'):
                            best_selectors['price'] = selectors['price']
                        if best_selectors['title'] and best_selectors['price']:
                            break
                except: continue

            return {
                'success': True,
                'url_pattern': search_pattern,
                'title_selector': best_selectors['title'],
                'price_selector': best_selectors['price'],
                'site_name': site_name
            }
        except Exception as e:
            return {'success': False, 'message': str(e), 'site_name': site_name}

    def _find_search_pattern(self, base_url):
        try:
            resp = self.session.get(base_url, headers=self.headers, timeout=10)
            soup = BeautifulSoup(resp.text, 'html.parser')
            for form in soup.find_all('form'):
                action = form.get('action', '')
                for inp in form.find_all('input'):
                    name = inp.get('name', '')
                    if name in ['keyword', 'query', 'q', 's', 'search_query', 'sword']:
                        if action:
                            return f"{urljoin(base_url, action)}?{name}={{}}"
        except: pass
        return None

    def _guess_platform_search_pattern(self, base_url):
        parsed = urlparse(base_url)
        domain = parsed.netloc.lower()
        if 'smartstore.naver.com' in domain:
            return urljoin(base_url + ("/" if not base_url.endswith("/") else ""), "search?q={}")
        return urljoin(base_url, "/product/search.html?keyword={}")

    def _detect_selectors(self, soup):
        selectors = {}
        title_candidates = ['strong[class^="_"]', 'span[class^="_"]', '.name a', '.prd_name a', '.item_name']
        for css in title_candidates:
            found = soup.select(css)
            if found:
                selectors['title'] = css
                break
        price_candidates = [('span[class^="_"]', 'span[class^="_"]'), ('[ec-data-price]', '[ec-data-price]::attr(ec-data-price)'), ('.price', '.price')]
        for css, selector in price_candidates:
            found = soup.select(css)
            if found:
                selectors['price'] = selector
                break
        return selectors
