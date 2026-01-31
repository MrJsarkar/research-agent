from duckduckgo_search import DDGS
import json
import time

print("Testing with default backend...")
try:
    with DDGS() as ddgs:
        # Default backend is usually 'api'
        results = list(ddgs.text("python", max_results=5))
        print(f"Found {len(results)} results")
        if results:
            print(results[0])
except Exception as e:
    print(f"Error with default backend: {e}")
