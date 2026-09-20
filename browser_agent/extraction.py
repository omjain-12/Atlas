import json
from .llm import LLMEngine


class ExtractionService:
    @staticmethod
    def extract_data(page_text: str, query: str, schema: str) -> str:
        """
        Secondary LLM call to extract structured data from page text based on a query and schema.
        """
        # Truncate text if too large for secondary model
        truncated_text = page_text[:20000] 
        
        prompt = f"""
Extract data from the following text based on this query: "{query}"

Expected Schema:
{schema}

Page Text:
{truncated_text}

Return strictly valid JSON matching the schema.
"""
        raw_response = LLMEngine.call(prompt)
        # Attempt to parse to ensure it's valid JSON
        try:
            parsed = json.loads(raw_response)
            return json.dumps(parsed)
        except json.JSONDecodeError:
            return f"Error: Extraction failed to produce valid JSON. Raw output: {raw_response[:200]}"
