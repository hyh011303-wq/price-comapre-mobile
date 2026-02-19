import sqlite3
import datetime

class DatabaseManager:
    def __init__(self, db_name="prices.db"):
        self.db_name = db_name
        self.create_tables()

    def get_connection(self):
        return sqlite3.connect(self.db_name)

    def create_tables(self):
        """Create necessary tables if they don't exist."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Sites configuration table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS sites (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    url_pattern TEXT NOT NULL,
                    title_selector TEXT,
                    price_selector TEXT,
                    is_active BOOLEAN DEFAULT 1
                )
            ''')
            
            # Products table (stores unique search keywords/products)
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS products (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL UNIQUE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Prices table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS prices (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    product_id INTEGER,
                    site_id INTEGER,
                    price REAL,
                    product_title TEXT,
                    product_url TEXT,
                    scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (product_id) REFERENCES products (id),
                    FOREIGN KEY (site_id) REFERENCES sites (id)
                )
            ''')
            
            # Search history table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS search_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    keyword TEXT NOT NULL UNIQUE,
                    last_searched_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            conn.commit()

    def add_site(self, name, url_pattern, title_selector, price_selector):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO sites (name, url_pattern, title_selector, price_selector)
                VALUES (?, ?, ?, ?)
            ''', (name, url_pattern, title_selector, price_selector))
            conn.commit()
            return cursor.lastrowid

    def get_sites(self):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM sites WHERE is_active = 1')
            return cursor.fetchall()
            
    def update_site(self, site_id, name, url_pattern, title_selector, price_selector):
         with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE sites 
                SET name=?, url_pattern=?, title_selector=?, price_selector=?
                WHERE id=?
            ''', (name, url_pattern, title_selector, price_selector, site_id))
            conn.commit()

    def get_or_create_product(self, name):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT id FROM products WHERE name = ?', (name,))
            row = cursor.fetchone()
            if row:
                return row[0]
            
            cursor.execute('INSERT INTO products (name) VALUES (?)', (name,))
            conn.commit()
            return cursor.lastrowid

    def add_price(self, product_id, site_id, price, product_title, product_url):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            # 오늘 이미 수집된 기록이 있는지 확인 (Local time 기준)
            cursor.execute('''
                SELECT id FROM prices 
                WHERE product_id = ? AND site_id = ? AND date(scraped_at, 'localtime') = date('now', 'localtime')
            ''', (product_id, site_id))
            row = cursor.fetchone()
            
            if row:
                # 같은 날짜 데이터가 있으면 업데이트 (최근 가격으로 덮어씀)
                cursor.execute('''
                    UPDATE prices 
                    SET price = ?, product_title = ?, product_url = ?, scraped_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                ''', (price, product_title, product_url, row[0]))
            else:
                # 데이터가 없으면 새로 삽입
                cursor.execute('''
                    INSERT INTO prices (product_id, site_id, price, product_title, product_url)
                    VALUES (?, ?, ?, ?, ?)
                ''', (product_id, site_id, price, product_title, product_url))
            conn.commit()
            
    def get_price_history(self, product_id):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT p.price, p.scraped_at, s.name 
                FROM prices p
                JOIN sites s ON p.site_id = s.id
                WHERE p.product_id = ?
                ORDER BY p.scraped_at
            ''', (product_id,))
            return cursor.fetchall()

    def get_all_products(self):
         with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT id, name FROM products ORDER BY name')
            return cursor.fetchall()

    def add_search_keyword(self, keyword):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO search_history (keyword, last_searched_at)
                VALUES (?, CURRENT_TIMESTAMP)
                ON CONFLICT(keyword) DO UPDATE SET last_searched_at=CURRENT_TIMESTAMP
            ''', (keyword,))
            conn.commit()

    def get_recent_keywords(self, limit=20):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT keyword FROM search_history ORDER BY last_searched_at DESC LIMIT ?', (limit,))
            return [row[0] for row in cursor.fetchall()]

    def delete_site(self, site_id):
        """Soft delete a site."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('UPDATE sites SET is_active = 0 WHERE id = ?', (site_id,))
            conn.commit()
