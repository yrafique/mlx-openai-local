# Real Web Search Integration Guide

## Current Status

Your web_search tool returns **mock results**. Here's how to make it real.

---

## Option 1: SerpAPI (Recommended)

### Why SerpAPI?
- ✅ Free tier: 100 searches/month
- ✅ Google search results
- ✅ Easy to use
- ✅ No scraping needed

### Setup

1. **Get API Key**
   ```bash
   # Visit: https://serpapi.com/users/sign_up
   # Get your free API key
   ```

2. **Add to .env**
   ```bash
   # Edit .env
   SERPAPI_KEY=your_api_key_here
   ```

3. **Update web_search_stub.py**
   ```python
   # server/tools/web_search_stub.py
   import os
   import requests

   def web_search(query: str, num_results: int = 3) -> dict:
       """Real web search using SerpAPI."""

       api_key = os.getenv("SERPAPI_KEY")
       if not api_key:
           return {
               "success": False,
               "error": "SERPAPI_KEY not set in .env"
           }

       try:
           response = requests.get(
               "https://serpapi.com/search",
               params={
                   "q": query,
                   "num": num_results,
                   "api_key": api_key,
                   "engine": "google"
               },
               timeout=10
           )

           if response.status_code == 200:
               data = response.json()
               results = []

               for item in data.get("organic_results", [])[:num_results]:
                   results.append({
                       "title": item.get("title"),
                       "url": item.get("link"),
                       "snippet": item.get("snippet")
                   })

               return {
                   "success": True,
                   "query": query,
                   "num_results": len(results),
                   "results": results
               }
           else:
               return {
                   "success": False,
                   "error": f"API error: {response.status_code}"
               }

       except Exception as e:
           return {
               "success": False,
               "error": str(e)
           }
   ```

4. **Test It**
   ```bash
   python3 test_direct_tool.py
   ```

---

## Option 2: DuckDuckGo (No API Key!)

### Setup

1. **Install package**
   ```bash
   pip install duckduckgo-search
   ```

2. **Update requirements.txt**
   ```bash
   echo "duckduckgo-search>=4.0.0" >> requirements.txt
   ```

3. **Update web_search_stub.py**
   ```python
   from duckduckgo_search import DDGS

   def web_search(query: str, num_results: int = 3) -> dict:
       """Real web search using DuckDuckGo (no API key needed)."""

       try:
           with DDGS() as ddgs:
               results = []

               for r in ddgs.text(query, max_results=num_results):
                   results.append({
                       "title": r.get("title"),
                       "url": r.get("href"),
                       "snippet": r.get("body")
                   })

               return {
                   "success": True,
                   "query": query,
                   "num_results": len(results),
                   "results": results
               }

       except Exception as e:
           return {
               "success": False,
               "error": str(e)
           }
   ```

---

## Option 3: Brave Search API

### Setup

1. **Get API Key**
   ```bash
   # Visit: https://brave.com/search/api/
   # Free tier: 2000 queries/month
   ```

2. **Add to .env**
   ```bash
   BRAVE_API_KEY=your_api_key_here
   ```

3. **Update web_search_stub.py**
   ```python
   import os
   import requests

   def web_search(query: str, num_results: int = 3) -> dict:
       """Real web search using Brave Search API."""

       api_key = os.getenv("BRAVE_API_KEY")
       if not api_key:
           return {"success": False, "error": "BRAVE_API_KEY not set"}

       try:
           response = requests.get(
               "https://api.search.brave.com/res/v1/web/search",
               params={"q": query, "count": num_results},
               headers={"X-Subscription-Token": api_key},
               timeout=10
           )

           if response.status_code == 200:
               data = response.json()
               results = []

               for item in data.get("web", {}).get("results", [])[:num_results]:
                   results.append({
                       "title": item.get("title"),
                       "url": item.get("url"),
                       "snippet": item.get("description")
                   })

               return {
                   "success": True,
                   "query": query,
                   "num_results": len(results),
                   "results": results
               }

       except Exception as e:
           return {"success": False, "error": str(e)}
   ```

---

## Comparison

| Service | Free Tier | API Key | Quality |
|---------|-----------|---------|---------|
| SerpAPI | 100/month | Required | ⭐⭐⭐⭐⭐ Google |
| DuckDuckGo | Unlimited | None | ⭐⭐⭐⭐ Good |
| Brave | 2000/month | Required | ⭐⭐⭐⭐ Good |

---

## Testing

After updating, test with:

```bash
python3 << 'EOF'
import sys
sys.path.insert(0, '/Users/yousef/Dev/mlx-openai-local')

from server.tools import execute_tool

result = execute_tool("web_search", {
    "query": "weather Ottawa Canada",
    "num_results": 3
})

print(result)
EOF
```

You should see **real search results**!

---

## Important Note

Even with real web search, **the 3B model still won't call it automatically**.

You'd need to:
1. Use a cloud API (GPT-4) for auto function calling
2. Or fine-tune the model
3. Or use rule-based detection in your app

But at least the tool will return **real data** when called!

---

## Recommended: DuckDuckGo

**Easiest to set up:**

```bash
# 1. Install
pip install duckduckgo-search

# 2. Update the tool file
# (copy code from Option 2 above)

# 3. Test
python3 test_direct_tool.py

# 4. Restart server
./scripts/orchestrate.sh --restart
```

**No API key needed, works immediately!**
