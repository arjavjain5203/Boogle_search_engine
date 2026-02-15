from boogle.query_engine.engine import QueryEngine

def verify_v5():
    print("Initializing Engine (Loading Index + Vector Store)...")
    try:
        engine = QueryEngine()
    except Exception as e:
        print(f"Error initializing engine: {e}")
        return

    # Test 1: Spelling (Raw Vocab)
    # "comput" should be corrected to "computer" if "computer" is in raw vocab
    query1 = "comput science"
    print(f"\nTest 1: Spelling '{query1}'")
    results1, corrected1, was_corrected1 = engine.search(query1)
    print(f"Corrected: {corrected1} (Was Corrected: {was_corrected1})")
    
    if "computer" in corrected1 or "compute" in corrected1:
        print("PASS: Corrected to 'computer' or 'compute'")
    else:
        print(f"FAIL: Predicted '{corrected1}'")

    # Test 2: Hybrid Search Components
    query2 = "computer science"
    print(f"\nTest 2: Hybrid Search '{query2}'")
    results2, _, _ = engine.search(query2)
    
    if results2:
        top = results2[0]
        print(f"Top: {top['metadata']['url']}")
        comps = top.get('components', {})
        print(f"Components: {comps}")
        
        if comps.get('vector', 0) > 0:
            print("PASS: Vector score contributed.")
        else:
            print("WARNING: Vector score is 0. (Maybe single doc or no similarity?)")
            
        if comps.get('bm25', 0) > 0:
            print("PASS: BM25 score contributed.")
    else:
        print("FAIL: No results.")

if __name__ == "__main__":
    verify_v5()
