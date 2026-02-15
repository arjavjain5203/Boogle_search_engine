from boogle.query_engine.engine import QueryEngine

def sanity_check():
    print("Initializing Engine...")
    engine = QueryEngine()
    
    query = "computer science"
    print(f"\nRunning sanity check for: '{query}'")
    
    results, corrected, was_corrected = engine.search(query)
    
    if not results:
        print("FAIL: No results found.")
        return
        
    top_doc = results[0]
    top_url = top_doc['metadata']['url']
    print(f"Top Result: {top_url}")
    print(f"Score: {top_doc['score']}")
    print(f"  - Text Score: {top_doc['text_score']}")
    print(f"  - Norm PageRank: {top_doc['norm_pagerank']}")
    
    if "wikipedia.org/wiki/Computer_science" in top_url:
        print("PASS: Top result captures 'Computer_science' article.")
    else:
        print("FAIL: Top result is NOT 'Computer_science' article.")
        
    # Check for utility pages
    for res in results[:5]:
        url = res['metadata']['url']
        if "Category:" in url or "Special:" in url or "Wikipedia:" in url:
            print(f"WARNING: Utility page found in top results: {url}")

if __name__ == "__main__":
    sanity_check()
