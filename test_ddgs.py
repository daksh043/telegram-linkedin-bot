from duckduckgo_search import DDGS
import json

def test_search(company_name):
    query = f'"{company_name}" CEO OR Founder OR HR linkedin profile'
    print(f"Searching: {query}")
    with DDGS() as ddgs:
        results = list(ddgs.text(query, max_results=3))
        print(json.dumps(results, indent=2))

test_search("OpenAI")
