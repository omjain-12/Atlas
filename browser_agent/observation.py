import json
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
from playwright.sync_api import Page
from .models import BrowserObservation, ElementNode, TabRef, BrowserAgentState
from .session import BrowserSessionManager


BUILD_DOM_TREE_JS = """
() => {
    let elementCounter = 0;
    const elements = [];
    
    function isInteractive(el) {
        const tag = el.tagName.toLowerCase();
        if (['a', 'button', 'input', 'select', 'textarea'].includes(tag)) return true;
        if (el.hasAttribute('onclick') || el.getAttribute('role') === 'button') return true;
        return false;
    }
    
    function isVisible(el) {
        const rect = el.getBoundingClientRect();
        return rect.width > 0 && rect.height > 0 && window.getComputedStyle(el).visibility !== 'hidden';
    }
    
    function walk(node) {
        if (node.nodeType === Node.ELEMENT_NODE) {
            if (isVisible(node) && isInteractive(node)) {
                const rect = node.getBoundingClientRect();
                
                // Assign a special attribute so we can find it later if needed
                node.setAttribute('data-browser-agent-ref', elementCounter);
                
                elements.push({
                    element_ref: elementCounter,
                    tag_name: node.tagName.toLowerCase(),
                    text: node.innerText?.trim() || node.value || '',
                    attributes: {
                        href: node.getAttribute('href') || '',
                        type: node.getAttribute('type') || '',
                        name: node.getAttribute('name') || '',
                        id: node.getAttribute('id') || '',
                        placeholder: node.getAttribute('placeholder') || ''
                    },
                    is_interactive: true,
                    is_visible: true,
                    bounding_box: {
                        x: Math.round(rect.x),
                        y: Math.round(rect.y),
                        width: Math.round(rect.width),
                        height: Math.round(rect.height)
                    }
                });
                elementCounter++;
            }
        }
        
        for (let child of node.childNodes) {
            walk(child);
        }
    }
    
    walk(document.body);
    return elements;
}
"""

class BrowserObservationManager:
    def __init__(self, session_manager: BrowserSessionManager):
        self.session = session_manager

    def observe(self) -> BrowserObservation:
        page = self.session.get_active_page()
        
        # Build tabs
        pages = self.session.get_pages()
        tabs = []
        active_tab_id = 0
        for i, p in enumerate(pages):
            tabs.append(TabRef(tab_id=i, title=p.title(), url=p.url))
            if p == page:
                active_tab_id = i

        # Inject script and get DOM elements
        try:
            elements_data = page.evaluate(BUILD_DOM_TREE_JS)
        except Exception:
            elements_data = []

        dom_elements = []
        for data in elements_data:
            dom_elements.append(ElementNode(**data))

        return BrowserObservation(
            url=page.url,
            title=page.title(),
            tabs=tabs,
            active_tab_id=active_tab_id,
            dom_elements=dom_elements
        )
