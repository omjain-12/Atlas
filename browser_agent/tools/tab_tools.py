from typing import Dict, Any, List
from ..session import BrowserSessionManager


class TabTools:
    def __init__(self, session: BrowserSessionManager):
        self.session = session

    def list_tabs(self) -> Dict[str, Any]:
        """Returns a summary of all open tabs."""
        tabs = []
        for i, page in enumerate(self.session.get_pages()):
            tabs.append({"tab_id": i, "title": page.title(), "url": page.url})
        return {"status": "success", "tabs": tabs}

    def switch_tab(self, tab_id: int) -> Dict[str, Any]:
        """Brings a specific tab to the foreground."""
        self.session.switch_tab(tab_id)
        return {"status": "success", "message": f"Switched to tab {tab_id}"}

    def close_tab(self, tab_id: int) -> Dict[str, Any]:
        """Closes a specific tab."""
        self.session.close_tab(tab_id)
        return {"status": "success", "message": f"Closed tab {tab_id}"}
