from typing import List, Optional, Dict, Any
from playwright.sync_api import sync_playwright, Browser, BrowserContext, Page


class BrowserSessionManager:
    """
    Manages the browser lifecycle, contexts, and tabs for the Browser Agent.
    """
    def __init__(self, headless: bool = False):
        self.headless = headless
        self._playwright = None
        self._browser: Optional[Browser] = None
        self._context: Optional[BrowserContext] = None
        self._active_page: Optional[Page] = None
        self.start()

    def start(self):
        if self._playwright is None:
            self._playwright = sync_playwright().start()
            self._browser = self._playwright.chromium.launch(headless=self.headless)
            self._context = self._browser.new_context()
            self._active_page = self._context.new_page()

    def stop(self):
        if self._context:
            self._context.close()
            self._context = None
        if self._browser:
            self._browser.close()
            self._browser = None
        if self._playwright:
            self._playwright.stop()
            self._playwright = None
        self._active_page = None

    def get_active_page(self) -> Page:
        if not self._active_page or self._active_page.is_closed():
            pages = self.get_pages()
            if pages:
                self._active_page = pages[-1]
            else:
                self._active_page = self._context.new_page()
        return self._active_page

    def get_pages(self) -> List[Page]:
        if not self._context:
            return []
        return self._context.pages

    def navigate(self, url: str, new_tab: bool = False) -> Page:
        if new_tab:
            page = self._context.new_page()
            self._active_page = page
        else:
            page = self.get_active_page()
            
        page.goto(url, wait_until="domcontentloaded")
        return page

    def close_tab(self, tab_id: int):
        pages = self.get_pages()
        if 0 <= tab_id < len(pages):
            page_to_close = pages[tab_id]
            is_active = (page_to_close == self._active_page)
            page_to_close.close()
            
            if is_active:
                remaining = self.get_pages()
                self._active_page = remaining[-1] if remaining else self._context.new_page()

    def switch_tab(self, tab_id: int):
        pages = self.get_pages()
        if 0 <= tab_id < len(pages):
            self._active_page = pages[tab_id]
            self._active_page.bring_to_front()
