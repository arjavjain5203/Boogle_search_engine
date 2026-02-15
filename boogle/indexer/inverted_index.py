import os
import json
import math
from collections import defaultdict, Counter
from boogle.config import Config
from boogle.processor.text_processor import TextProcessor
from boogle.vectors.store import VectorStore

class InvertedIndex:
    def __init__(self):
        self.index = defaultdict(list)  # term -> [(doc_id, tf), ...]
        self.doc_metadata = {}  # doc_id -> {url, title, length}
        self.processor = TextProcessor()
        self.vector_store = VectorStore()
        self.raw_vocabulary = Counter() # raw_word -> frequency
        self.storage_path = Config.STORAGE_PATH
        self.index_path = os.path.join(self.storage_path, 'index')
        
        if not os.path.exists(self.index_path):
            os.makedirs(self.index_path)
        
    def build_index(self):
        """
        Iterate over raw HTML files, process them, and build the index.
        """
        raw_path = os.path.join(self.storage_path, 'raw')
        url_map_path = os.path.join(self.storage_path, 'url_map.json')
        
        if not os.path.exists(url_map_path):
            print("No URL map found. Has the crawler run?")
            return

        with open(url_map_path, 'r') as f:
            url_map = json.load(f)
            
        print("Building index (Lexical + Vector)...")
        
        # In this simple implementation, doc_id is the hash filename (without .html)
        for filename in os.listdir(raw_path):
            if not filename.endswith('.html'):
                continue
                
            doc_id = filename.replace('.html', '')
            file_path = os.path.join(raw_path, filename)
            
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    
                # New signature: return title, first_para, text, title_stemmed, first_para_stemmed, body_stemmed, raw_words
                title, first_para, text, title_tokens, first_para_tokens, body_tokens, raw_words = self.processor.process_document(content)
                url = url_map.get(doc_id, "Unknown URL")
                
                # Update metadata
                self.doc_metadata[doc_id] = {
                    'url': url,
                    'title': title,
                    'length': len(title_tokens) + len(first_para_tokens) + len(body_tokens)
                }
                
                # Update Raw Vocabulary
                self.raw_vocabulary.update(raw_words)
                
                # Add to Vector Store (Use Title + First Paragraph for embedding)
                vector_text = f"{title}. {first_para}"
                self.vector_store.add_document(doc_id, vector_text)
                
                # Calculate Weighted Term Frequencies
                # TF = BodyTF + (TitleTF * TitleWeight) + (FirstParaTF * FirstParaWeight)
                term_freqs = defaultdict(float)
                
                for token in body_tokens:
                    term_freqs[token] += 1.0
                    
                for token in title_tokens:
                    term_freqs[token] += Config.TITLE_WEIGHT
                    
                for token in first_para_tokens:
                    term_freqs[token] += 3.0 # Hardcoded First Para Weight
                
                # Update Index
                for term, weighted_count in term_freqs.items():
                    self.index[term].append((doc_id, weighted_count))
            
            except Exception as e:
                print(f"Error indexing {filename}: {e}")

        self.save_index()
        self.save_vocabulary()
        self.vector_store.save()
        print(f"Index built with {len(self.index)} terms and {len(self.doc_metadata)} documents.")

    def save_vocabulary(self):
        """Save raw vocabulary for spelling correction"""
        vocab_path = os.path.join(self.index_path, 'raw_vocabulary.json')
        # Filter for reasonable size/quality? For 200 docs, keep all.
        # But let's dump as list of tokens or dict with counts?
        # Requirement: "Extract words BEFORE stemming... Store frequency counts... frequency weighting"
        # So we save the dict.
        with open(vocab_path, 'w') as f:
            json.dump(dict(self.raw_vocabulary), f)

    def save_index(self):
        """
        Persist index and metadata to disk.
        """
        # Save inverted index
        with open(os.path.join(self.index_path, 'inverted_index.json'), 'w') as f:
            json.dump(self.index, f)
            
        # Save metadata
        with open(os.path.join(self.index_path, 'doc_metadata.json'), 'w') as f:
            json.dump(self.doc_metadata, f, indent=2)

    def load_index(self):
        """
        Load index from disk.
        """
        idx_file = os.path.join(self.index_path, 'inverted_index.json')
        meta_file = os.path.join(self.index_path, 'doc_metadata.json')
        
        if os.path.exists(idx_file):
            with open(idx_file, 'r') as f:
                self.index = json.load(f)
        
        if os.path.exists(meta_file):
            with open(meta_file, 'r') as f:
                self.doc_metadata = json.load(f)
        
        # Load vector store
        self.vector_store.load()

if __name__ == "__main__":
    indexer = InvertedIndex()
    indexer.build_index()
