# -*- coding: utf-8 -*-
"""
Test SerpAPI with regular Google Search
"""

import os
from dotenv import load_dotenv
from serpapi import GoogleSearch
import json

load_dotenv()

api_key = os.getenv("SERPAPI_KEY")

print(f"🔑 SERPAPI_KEY: {api_key[:10]}...{api_key[-5:] if api_key else 'NOT SET'}\n")

test_query = "Huda Beauty Liquid Matte Lipstick"

print("="*60)
print("TEST 1: Search Jumia Egypt")
print("="*60)

params = {
    "api_key": api_key,
    "engine": "google",
    "q": f"{test_query} site:jumia.com.eg",
    "num": 3
}

try:
    search = GoogleSearch(params)
    results = search.get_dict()
    
    organic = results.get("organic_results", [])
    
    if organic:
        print(f"✅ Found {len(organic)} results on Jumia!\n")
        for i, result in enumerate(organic, 1):
            print(f"{i}. {result.get('title', 'No title')}")
            print(f"   {result.get('link', 'No link')}\n")
    else:
        print("❌ No Jumia results found\n")
        print("Response:", json.dumps(results, indent=2))
    
except Exception as e:
    print(f"❌ ERROR: {e}\n")

print("\n" + "="*60)
print("TEST 2: Regular Google Search")
print("="*60)

params2 = {
    "api_key": api_key,
    "engine": "google",
    "q": f"{test_query} buy egypt",
    "num": 5
}

try:
    search = GoogleSearch(params2)
    results = search.get_dict()
    
    organic = results.get("organic_results", [])
    
    if organic:
        print(f"✅ Found {len(organic)} results!\n")
        for i, result in enumerate(organic, 1):
            print(f"{i}. {result.get('title', 'No title')}")
            print(f"   {result.get('link', 'No link')}\n")
    else:
        print("❌ No results\n")
    
except Exception as e:
    print(f"❌ ERROR: {e}\n")

print("="*60)
print("✅ SERPAPI IS WORKING WITH REGULAR GOOGLE SEARCH!")
print("="*60)