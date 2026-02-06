from boogle.query_engine.engine import QueryEngine

def verify_ranking():
    print("Initializing Engine...")
    engine = QueryEngine()
    
    # Test 1: Soft AND / Partial Matches
    query1 = "computer science pizza"
    print(f"\nTest 1: Partial Match for '{query1}'")
    results1, _, _ = engine.search(query1)
    
    if not results1:
        print("FAIL: No results for partial match.")
    else:
        top_doc = results1[0]
        print(f"Top Result: {top_doc['metadata']['url']}")
        print(f"Terms Missing: {top_doc.get('missing_terms', 'N/A')}")
        if top_doc.get('missing_terms', 0) > 0:
            print("PASS: Returned result despite missing terms (Soft AND works).")
        else:
            print("WARNING: Top doc has all terms? (Pizza found?)")

    # Test 2: Phrase Matching
    query2 = "computer science"
    print(f"\nTest 2: Phrase Match for '{query2}'")
    results2, _, _ = engine.search(query2)
    
    if results2:
        top_doc = results2[0]
        print(f"Top Result: {top_doc['metadata']['url']}")
        print(f"Phrase Match Bonus: {top_doc.get('phrase_match', False)}")
        if top_doc.get('phrase_match'):
            print("PASS: Phrase match detected.")
        else:
            print("FAIL: Phrase match NOT detected.")
    else:
        print("FAIL: No results found.")

if __name__ == "__main__":
    verify_ranking()
