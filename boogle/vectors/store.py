import os
import json
import numpy as np
import faiss
from sentence_transformers import SentenceTransformer
from boogle.config import Config

class VectorStore:
    def __init__(self):
        self.model_name = 'all-MiniLM-L6-v2'
        self.model = SentenceTransformer(self.model_name)
        self.dimension = 384  # Dimension for all-MiniLM-L6-v2
        self.index = faiss.IndexFlatL2(self.dimension)
        self.doc_ids = [] # map index id to doc_id
        self.storage_path = os.path.join(Config.STORAGE_PATH, 'vectors')
        
        if not os.path.exists(self.storage_path):
            os.makedirs(self.storage_path)
            
    def add_document(self, doc_id, text):
        """
        Generate embedding for text and add to index.
        """
        if not text.strip():
            return
            
        embedding = self.model.encode([text])[0]
        # Normalize for cosine similarity (if using IP index, but L2 is fine for relative ranking too if normalized? 
        # Actually L2 distance is related to Cosine Sim for normalized vectors. 
        # For simplicity, let's keep it simple. L2 is fine.)
        # But usually for semantic search cosine similarity is preferred.
        # Faiss IP (Inner Product) == Cosine Similarity if vectors are normalized.
        
        # Normalize
        faiss.normalize_L2(embedding.reshape(1, -1))
        
        self.index.add(np.array([embedding], dtype=np.float32))
        self.doc_ids.append(doc_id)
        
    def search(self, query, k=10):
        """
        Return list of (doc_id, score)
        """
        embedding = self.model.encode([query])[0]
        faiss.normalize_L2(embedding.reshape(1, -1))
        
        # FAISS search
        distances, indices = self.index.search(np.array([embedding], dtype=np.float32), k)
        
        results = []
        for i, idx in enumerate(indices[0]):
            if idx != -1 and idx < len(self.doc_ids):
                # Convert L2 distance to something like a similarity score?
                # Since vectors are normalized, L2 = 2 - 2*IP. 
                # IP (Cosine) is better for ranking score. 
                # Let's just trust that smaller L2 is better. 
                # But for our hybrid score we need a "similarity" score (higher is better).
                # Sim = 1 / (1 + dist) or similar? 
                # Or just use Inner Product index?
                # Let's switch to IndexFlatIP for simplicity in next iteration or just convert here.
                # Cosine Sim = 1 - (L2^2) / 2
                score = 1 - (distances[0][i] ** 2) / 2
                results.append((self.doc_ids[idx], float(score)))
                
        return results

    def save(self):
        faiss.write_index(self.index, os.path.join(self.storage_path, 'index.faiss'))
        with open(os.path.join(self.storage_path, 'doc_ids.json'), 'w') as f:
            json.dump(self.doc_ids, f)
            
    def load(self):
        index_path = os.path.join(self.storage_path, 'index.faiss')
        if os.path.exists(index_path):
            self.index = faiss.read_index(index_path)
        
        ids_path = os.path.join(self.storage_path, 'doc_ids.json')
        if os.path.exists(ids_path):
            with open(ids_path, 'r') as f:
                self.doc_ids = json.load(f)
