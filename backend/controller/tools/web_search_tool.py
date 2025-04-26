from duckduckgo_search import DDGS
from agents import function_tool

class WebSearchTool:
    @function_tool
    def web_search(query: str, max_results: int = 3) -> str:
        with DDGS() as ddgs:
            results = ddgs.text(query, max_results=max_results)
            if not results:
                return "No results found."
            return results
