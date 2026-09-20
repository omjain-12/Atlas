import time
from typing import Dict, Any
from ..session import BrowserSessionManager


class CoreTools:
    def __init__(self, session: BrowserSessionManager):
        self.session = session

    def get_page_info(self) -> Dict[str, Any]:
        """Returns lightweight metadata about the page without pulling the full DOM."""
        page = self.session.get_active_page()
        try:
            ready_state = page.evaluate("document.readyState")
        except Exception:
            ready_state = "unknown"
        return {"url": page.url, "title": page.title(), "ready_state": ready_state}

    def navigate(self, url: str, new_tab: bool = False) -> Dict[str, Any]:
        """Navigates the browser to a URL. Optionally opens it in a new tab."""
        page = self.session.navigate(url, new_tab)
        return {"status": "success", "url": page.url}

    def search(self, query: str, engine: str = "google") -> Dict[str, Any]:
        """Convenience method to search using a search engine."""
        url = f"https://www.google.com/search?q={query}"
        self.session.navigate(url)
        return {"status": "success", "message": f"Searched {engine} for {query}"}

    def go_back(self) -> Dict[str, Any]:
        """Standard browser history control - Back."""
        self.session.get_active_page().go_back()
        return {"status": "success", "message": "Navigated back"}

    def go_forward(self) -> Dict[str, Any]:
        """Standard browser history control - Forward."""
        self.session.get_active_page().go_forward()
        return {"status": "success", "message": "Navigated forward"}

    def refresh(self) -> Dict[str, Any]:
        """Standard browser history control - Refresh."""
        self.session.get_active_page().reload()
        return {"status": "success", "message": "Refreshed page"}

    def wait(self, seconds: float) -> Dict[str, Any]:
        """Pauses the agent to wait for animations or network requests to settle."""
        # Using synchronous sleep since the controller is synchronous
        time.sleep(min(seconds, 30))
        return {"status": "success", "message": f"Waited {seconds} seconds"}
