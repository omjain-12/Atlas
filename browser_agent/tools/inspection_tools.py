from typing import Dict, Any, List
from ..session import BrowserSessionManager
from ..extraction import ExtractionService
import re


class InspectionTools:
    def __init__(self, session: BrowserSessionManager):
        self.session = session

    def _get_element_selector(self, element_ref: int) -> str:
        return f"[data-browser-agent-ref='{element_ref}']"

    def search_page(self, pattern: str) -> Dict[str, Any]:
        """Fast text search on the page returning matches and surrounding text."""
        page = self.session.get_active_page()
        # Very simple implementation grabbing page text and regexing
        text = page.evaluate("document.body.innerText")
        matches = []
        # Find context around match
        for m in re.finditer(re.escape(pattern), text, re.IGNORECASE):
            start = max(0, m.start() - 50)
            end = min(len(text), m.end() + 50)
            matches.append(text[start:end].replace('\n', ' ').strip())
            
        return {"status": "success", "matches": matches[:10]} # Limit to 10

    def find_elements(self, selector: str) -> Dict[str, Any]:
        """Evaluates a CSS selector and returns data about matching elements."""
        page = self.session.get_active_page()
        elements = page.eval_on_selector_all(
            selector, 
            "els => els.map(e => ({tag: e.tagName, text: e.innerText, href: e.href}))"
        )
        return {"status": "success", "elements": elements}

    def get_dropdown_options(self, element_ref: int) -> Dict[str, Any]:
        """Returns all <option> values for a select element."""
        page = self.session.get_active_page()
        selector = self._get_element_selector(element_ref)
        options = page.eval_on_selector(
            selector,
            "el => Array.from(el.options).map(o => o.text)"
        )
        return {"status": "success", "options": options}

    def extract_data(self, query: str, schema: str) -> Dict[str, Any]:
        """Uses a secondary LLM to extract structured data from the page text based on a schema."""
        page = self.session.get_active_page()
        page_text = page.evaluate("document.body.innerText")
        
        result_json = ExtractionService.extract_data(page_text, query, schema)
        return {"status": "success", "extracted_data": result_json}
