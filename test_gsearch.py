from googlesearch import search
import json

def test_search():
    query = 'site:linkedin.com/in "Tata Group" "HR" OR "Recruiter" OR "Manager"'
    print(f"Searching: {query}")
    results = []
    try:
        # advanced=True returns dicts with url, title, description
        for res in search(query, num_results=3, advanced=True):
            results.append({
                "url": res.url,
                "title": res.title,
                "description": res.description
            })
        print(json.dumps(results, indent=2))
    except Exception as e:
        print(f"Error: {e}")

test_search()
