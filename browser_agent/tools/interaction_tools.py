from typing import Dict, Any, Optional
from ..session import BrowserSessionManager


class InteractionTools:
    def __init__(self, session: BrowserSessionManager):
        self.session = session

    def _get_element_selector(self, element_ref: int) -> str:
        """Helper to get a CSS selector for an element by its data attribute assigned during observation."""
        return f"[data-browser-agent-ref='{element_ref}']"

    def click(self, element_ref: int) -> Dict[str, Any]:
        """Clicks an interactive element identified by its reference index."""
        page = self.session.get_active_page()
        selector = self._get_element_selector(element_ref)
        page.locator(selector).first.click(timeout=3000)
        return {"status": "success", "message": f"Clicked element {element_ref}"}

    def input(self, element_ref: int, text: str, clear: bool = True) -> Dict[str, Any]:
        """Types text into a specific input field."""
        page = self.session.get_active_page()
        selector = self._get_element_selector(element_ref)
        locator = page.locator(selector).first
        if clear:
            locator.fill("")
        locator.type(text, delay=50)
        return {"status": "success", "message": f"Input '{text}' into element {element_ref}"}

    def send_keys(self, keys: str) -> Dict[str, Any]:
        """Dispatches a raw keyboard event (e.g. Enter, Escape, Tab)."""
        page = self.session.get_active_page()
        page.keyboard.press(keys)
        return {"status": "success", "message": f"Pressed {keys}"}

    def scroll(self, direction: str, amount: str = "page") -> Dict[str, Any]:
        """Scrolls the active window."""
        page = self.session.get_active_page()
        pixels = 1000 if amount == "page" else 300
        if direction.lower() == "up":
            pixels = -pixels
            
        page.evaluate(f"window.scrollBy(0, {pixels})")
        return {"status": "success", "message": f"Scrolled {direction}"}

    def select_dropdown(self, element_ref: int, option_text: str) -> Dict[str, Any]:
        """Selects a specific string option from a native HTML <select> element."""
        page = self.session.get_active_page()
        selector = self._get_element_selector(element_ref)
        page.locator(selector).first.select_option(label=option_text, timeout=3000)
        return {"status": "success", "message": f"Selected '{option_text}' on {element_ref}"}

    def hover(self, element_ref: int) -> Dict[str, Any]:
        """Moves the mouse cursor over an element."""
        page = self.session.get_active_page()
        selector = self._get_element_selector(element_ref)
        page.locator(selector).first.hover(timeout=3000)
        return {"status": "success", "message": f"Hovered over {element_ref}"}

    def upload_file(self, element_ref: int, file_path: str) -> Dict[str, Any]:
        """Attaches a local file to a file input."""
        page = self.session.get_active_page()
        selector = self._get_element_selector(element_ref)
        page.locator(selector).first.set_input_files(file_path, timeout=3000)
        return {"status": "success", "message": f"Uploaded file to {element_ref}"}
