import json
import os
import networkx as nx
from boogle.config import Config

class PageRank:
    def __init__(self):
        self.storage_path = Config.STORAGE_PATH
        self.link_graph_path = os.path.join(self.storage_path, 'link_graph.json')
        self.pagerank_path = os.path.join(self.storage_path, 'pagerank.json')
        self.damping_factor = 0.85
        self.iterations = 20
        
    def compute_pagerank(self):
        """
        Compute PageRank scores for all pages in the link graph.
        """
        if not os.path.exists(self.link_graph_path):
            print("Link graph not found.")
            return

        with open(self.link_graph_path, 'r') as f:
            link_graph = json.load(f)
            
        print(f"Computing PageRank for {len(link_graph)} nodes...")
        
        # Build NetworkX graph
        G = nx.DiGraph()
        
        # Add nodes and edges
        for source, targets in link_graph.items():
            G.add_node(source)
            for target in targets:
                # Only add edges if target is also in our crawled set (link graph keys)
                # Or add them anyway? PageRank handles dangling nodes, but strictly 
                # we only have scores for pages we know about. 
                # Let's add edge only if target was visited (is a key in link_graph)
                # effectively a subgraph of the web.
                if target in link_graph:
                    G.add_edge(source, target)
                else:
                    # If we don't include external links, it's a closed system. 
                    # If we do, we might have millions of dangling nodes.
                    # Implementation choice: Closed system for now.
                    pass
                    
        # Compute PageRank
        try:
            scores = nx.pagerank(G, alpha=self.damping_factor, max_iter=self.iterations)
        except Exception as e:
            print(f"Error computing PageRank: {e}")
            # Fallback to uniform distribution if empty or error
            scores = {node: 1.0/len(link_graph) for node in link_graph}
            
        # Store scores
        # We need to map actual URLs to scores. 
        # But wait, our Doc IDs are hashes. We need to map URL -> Score -> Doc ID or 
        # just store URL -> Score and look it up later.
        # The Indexer stores Doc Metadata: Hash -> URL. 
        # So Query Engine can go Doc Hash -> URL -> PageRank.
        
        with open(self.pagerank_path, 'w') as f:
            json.dump(scores, f, indent=2)
            
        print("PageRank computation finished.")

if __name__ == "__main__":
    pr = PageRank()
    pr.compute_pagerank()
