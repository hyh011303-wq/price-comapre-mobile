import flet as ft
import threading
import datetime
import asyncio
from database_manager import DatabaseManager
from scraper import PriceScraper
from auto_discovery import SiteAnalyzer

# Colors
PRIMARY = ft.Colors.INDIGO_400
BG_COLOR = "#121212"
CARD_BG = "#1E1E1E"

class PriceCompareMobile:
    def __init__(self, page: ft.Page):
        self.page = page
        self.page.title = "측기 가격비교"
        self.page.theme_mode = ft.ThemeMode.DARK
        self.page.padding = 0
        self.page.bgcolor = BG_COLOR
        
        # Robust initialization
        try:
            # On Android, relative path might be tricky, but usually works in app dir.
            # Using a simple try-except to catch DB errors.
            self.db = DatabaseManager("prices_mobile.db")
            self.scraper = PriceScraper()
            self.analyzer = SiteAnalyzer()
            self.last_searched = None
            self.setup_ui()
        except Exception as e:
            self.show_critical_error(str(e))

    def show_critical_error(self, error_msg):
        self.page.add(
            ft.Container(
                content=ft.Column([
                    ft.Icon(ft.Icons.ERROR_OUTLINE, color=ft.Colors.RED_400, size=50),
                    ft.Text("앱 초기화 중 오류가 발생했습니다:", weight="bold"),
                    ft.Text(error_msg, color=ft.Colors.RED_200, selectable=True),
                    ft.ElevatedButton("다시 시도", on_click=lambda _: self.page.window_reload())
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                alignment=ft.alignment.center,
                expand=True
            )
        )

    def setup_ui(self):
        # Navigation Bar
        self.tabs = ft.Tabs(
            selected_index=0,
            animation_duration=300,
            tabs=[
                ft.Tab(text="상품검색", icon=ft.Icons.SEARCH),
                ft.Tab(text="가격추이", icon=ft.Icons.SHOW_CHART),
                ft.Tab(text="쇼핑몰 설정", icon=ft.Icons.SETTINGS),
            ],
            expand=1,
            on_change=self.on_tab_change
        )

        # Tab 1: Search
        self.search_input = ft.TextField(
            hint_text="검색 상품명 입력",
            expand=True,
            border_radius=10,
            on_submit=self.start_search
        )
        self.search_results = ft.ListView(expand=True, spacing=10, padding=10)
        self.search_view = ft.Column([
            ft.Container(
                content=ft.Row([self.search_input, ft.IconButton(icon=ft.Icons.SEARCH, on_click=self.start_search)]),
                padding=10
            ),
            self.search_results
        ], visible=True)

        # Tab 2: History
        self.product_dropdown = ft.Dropdown(
            label="상품 선택",
            on_change=self.on_product_select,
            border_radius=10
        )
        self.chart_container = ft.Container(expand=True, padding=10)
        self.history_view = ft.Column([
            ft.Container(content=self.product_dropdown, padding=10),
            self.chart_container
        ], visible=False)

        # Tab 3: Settings
        self.site_list = ft.ListView(expand=True, spacing=10, padding=10)
        self.settings_view = ft.Column([
            ft.Container(content=ft.Text("쇼핑몰 관리", size=20, weight="bold"), padding=10),
            self.site_list,
            ft.FloatingActionButton(icon=ft.Icons.ADD, on_click=self.show_add_site_dialog)
        ], visible=False)

        self.page.add(
            ft.AppBar(
                title=ft.Text("Price Smart Mobile", weight="bold"),
                bgcolor=ft.Colors.SURFACE_VARIANT,
                center_title=True,
            ),
            ft.Container(
                content=ft.Stack([self.search_view, self.history_view, self.settings_view]),
                expand=True
            ),
            self.tabs
        )
        self.load_sites()
        self.load_products()

    def on_tab_change(self, e):
        idx = self.tabs.selected_index
        self.search_view.visible = (idx == 0)
        self.history_view.visible = (idx == 1)
        self.settings_view.visible = (idx == 2)
        
        if idx == 1:
            self.load_products()
            if self.last_searched:
                self.product_dropdown.value = self.last_searched
                self.on_product_select(None)
        
        self.page.update()

    def load_sites(self):
        try:
            sites = self.db.get_sites()
            self.site_list.controls.clear()
            for site in sites:
                self.site_list.controls.append(
                    ft.Card(
                        content=ft.ListTile(
                            leading=ft.Icon(ft.Icons.STORE),
                            title=ft.Text(site[1]),
                            subtitle=ft.Text(site[2]),
                            trailing=ft.IconButton(ft.Icons.DELETE, on_click=lambda x, sid=site[0]: self.delete_site(sid))
                        )
                    )
                )
            self.page.update()
        except: pass

    def delete_site(self, sid):
        self.db.delete_site(sid)
        self.load_sites()

    def start_search(self, e):
        keyword = self.search_input.value
        if not keyword: return
        self.last_searched = keyword
        self.search_results.controls.clear()
        self.search_results.controls.append(ft.ProgressBar(color=PRIMARY))
        self.page.update()
        
        threading.Thread(target=self.run_scraping, args=(keyword,), daemon=True).start()

    def run_scraping(self, keyword):
        pid = self.db.get_or_create_product(keyword)
        sites = self.db.get_sites()
        results = []
        for site in sites:
            site_config = {'id': site[0], 'name': site[1], 'url_pattern': site[2], 'title_selector': site[3], 'price_selector': site[4]}
            res = self.scraper.scrape_site(site_config, keyword)
            if res['success']:
                self.db.add_price(pid, site[0], res['price'], res['product_title'], res['url'])
                results.append(res)
        
        def update_ui():
            self.search_results.controls.clear()
            if not results:
                self.search_results.controls.append(ft.Text("검색 결과가 없습니다."))
            else:
                for r in results:
                    self.search_results.controls.append(
                        ft.Card(
                            content=ft.Container(
                                content=ft.Column([
                                    ft.ListTile(
                                        title=ft.Text(r['product_title'], max_lines=2, weight="bold"),
                                        subtitle=ft.Text(r['site_name']),
                                        trailing=ft.Text(f"{r['price']:,.0f}원", size=18, color=ft.Colors.AMBER_400, weight="bold")
                                    ),
                                    ft.TextButton("사이트 방문", on_click=lambda x, url=r['url']: self.page.launch_url(url))
                                ], spacing=0),
                                padding=5
                            )
                        )
                    )
            self.page.update()
        
        self.page.run_threadsafe(update_ui)

    def load_products(self):
        try:
            products = self.db.get_all_products()
            self.product_dropdown.options = [ft.dropdown.Option(name) for pid, name in products]
            self.page.update()
        except: pass

    def on_product_select(self, e):
        name = self.product_dropdown.value
        if not name: return
        products = self.db.get_all_products()
        pid = next((p[0] for p in products if p[1] == name), None)
        if pid:
            history = self.db.get_price_history(pid)
            self.update_chart(history)

    def update_chart(self, history):
        if not history:
            self.chart_container.content = ft.Text("데이터가 부족합니다.")
            self.page.update()
            return

        # Simple LineChart implementation
        sites_data = {}
        for price, date_str, site_name in history:
            try:
                dt = datetime.datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S")
                if site_name not in sites_data: sites_data[site_name] = []
                sites_data[site_name].append((dt.timestamp(), price))
            except: continue

        data_series = []
        colors = [ft.Colors.BLUE, ft.Colors.RED, ft.Colors.GREEN, ft.Colors.AMBER, ft.Colors.PURPLE]
        for i, (site, points) in enumerate(sites_data.items()):
            color = colors[i % len(colors)]
            data_series.append(
                ft.LineChartData(
                    data_points=[ft.LineChartDataPoint(p[0], p[1]) for p in points],
                    stroke_width=2,
                    color=color,
                    curved=True,
                    marker_size=6
                )
            )

        self.chart_container.content = ft.LineChart(
            data_series=data_series,
            border=ft.border.all(1, ft.Colors.with_opacity(0.1, ft.Colors.ON_SURFACE)),
            horizontal_grid_lines=ft.ChartGridLines(interval=10000, width=1, color=ft.Colors.with_opacity(0.1, ft.Colors.ON_SURFACE)),
            tooltip_bgcolor=ft.Colors.with_opacity(0.8, ft.Colors.BLUE_GREY_900),
            expand=True
        )
        self.page.update()

    def show_add_site_dialog(self, e):
        url_input = ft.TextField(label="상점 메인 URL")
        
        def save_site(e):
            res = self.analyzer.analyze(url_input.value)
            if res['success']:
                self.db.add_site(res['site_name'], res['url_pattern'], res['title_selector'], res['price_selector'])
                self.load_sites()
                dialog.open = False
                self.page.update()
            else:
                url_input.error_text = "분석 실패"
                self.page.update()

        dialog = ft.AlertDialog(
            title=ft.Text("새 쇼핑몰 추가"),
            content=url_input,
            actions=[ft.TextButton("분석 및 저장", on_click=save_site)]
        )
        self.page.dialog = dialog
        dialog.open = True
        self.page.update()

if __name__ == "__main__":
    def main(page: ft.Page):
        PriceCompareMobile(page)
    ft.app(target=main)
