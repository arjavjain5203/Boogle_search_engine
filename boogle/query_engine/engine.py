import math
import os
import json
from collections import defaultdict
from boogle.config import Config
from boogle.processor.text_processor import TextProcessor
from boogle.indexer.inverted_index import InvertedIndex

from boogle.query_engine.spelling import SpellingCorrector

class QueryEngine:
    def __init__(self):
        self.processor = TextProcessor()
        self.indexer = InvertedIndex()
        self.indexer.load_index()
        self.spelling_corrector = SpellingCorrector()
        
        self.alpha = Config.RANKING_ALPHA
        self.beta = Config.RANKING_BETA
        
        self.pagerank_scores = self.load_pagerank()
        
        # Precompute avg_dl for BM25
        self.avg_dl = 0
        self.doc_count = len(self.indexer.doc_metadata)
        if self.doc_count > 0:
            total_len = sum(meta['length'] for meta in self.indexer.doc_metadata.values())
            self.avg_dl = total_len / self.doc_count

    def load_pagerank(self):
        path = os.path.join(Config.STORAGE_PATH, 'pagerank.json')
        if os.path.exists(path):
            with open(path, 'r') as f:
                return json.load(f)
        return {}

    def search(self, query):
        """
        Execute a hybrid search query and return ranked results.
        Returns: (results_list, corrected_query, was_corrected)
        """
        # 1. Spell Correction (Raw Vocab)
        corrected_query, was_corrected = self.spelling_corrector.correct_query(query)
        search_query = corrected_query if was_corrected else query
        
        # 2. Vector Search (Semantic Candidates)
        # We assume VectorStore is loaded in Indexer
        # If not, we might need to load it here or rely on Indexer
        # Current design: QueryEngine -> InvertedIndex -> VectorStore
        # Let's ensure VectorStore is ready
        if not hasattr(self.indexer, 'vector_store'):
            # Should be initialized in InvertedIndex __init__
            pass

        semantic_candidates = []
        if self.indexer.vector_store:
            # Returns [(doc_id, sim_score)]
            semantic_candidates = self.indexer.vector_store.search(search_query, k=20)
            
        semantic_docs = {doc_id: score for doc_id, score in semantic_candidates}

        # 3. Lexical Search (Keyword Candidates)
        query_tokens = self.processor.tokenize(search_query)
        
        lexical_docs = set()
        term_docs_map = {}
        for term in query_tokens:
            if term in self.indexer.index:
                docs = {doc_id for doc_id, _ in self.indexer.index[term]}
                term_docs_map[term] = docs
                lexical_docs.update(docs)
            else:
                term_docs_map[term] = set()

        # 4. Merge Candidates (Union)
        all_candidates = lexical_docs.union(semantic_docs.keys())
        
        if not all_candidates:
             return [], corrected_query, was_corrected

        # Precompute max PR
        max_pr = 1.0
        if self.pagerank_scores:
            max_pr = max(self.pagerank_scores.values()) if self.pagerank_scores else 1.0
            
        # 5. Score Candidates
        scores = []
        original_query_str = query.lower()
        
        for doc_id in all_candidates:
            # Metadata
            if doc_id not in self.indexer.doc_metadata:
                continue
                
            # -- Lexical Score (BM25) --
            present_terms = [t for t in query_tokens if doc_id in term_docs_map.get(t, set())]
            missing_terms = len(query_tokens) - len(present_terms)
            text_score = self.calculate_bm25(doc_id, present_terms) if present_terms else 0.0
            
            # Penalties/Bonuses
            completeness_penalty = 0.5 ** missing_terms if query_tokens else 1.0
            full_match_bonus = 1.2 if missing_terms == 0 and query_tokens else 1.0
            
            phrase_bonus = 1.0
            if len(present_terms) >= len(query_tokens) * 0.5 and len(query_tokens) > 1:
                if self.check_phrase_match(doc_id, original_query_str):
                    phrase_bonus = 1.5

            adjusted_text_score = text_score * completeness_penalty * full_match_bonus * phrase_bonus
            
            # -- Semantic Score --
            # Vector score is roughly cosine similarity [0, 1] (if using Cosine) or 1 - L2_dist/2. 
            # From VectorStore implementation, we returned 1 - L2^2 / 2.
            # Let's clip it to [0, 1] just in case
            vector_score = max(0.0, min(1.0, semantic_docs.get(doc_id, 0.0)))
            
            # -- PageRank --
            url = self.indexer.doc_metadata[doc_id]['url']
            raw_pr = self.pagerank_scores.get(url, 0.0)
            norm_pr = raw_pr / max_pr if max_pr > 0 else 0
            effective_pr_score = norm_pr * 10
            
            # -- Final Combination --
            # Weighted Sum:
            # BM25 is usually > 1.0. Vector is 0-1. PR is scaled to ~0-10.
            # Let's weight them:
            # Final = (Lexical * 0.7) + (Vector * 5.0 * 0.3) + (PR * 0.15)
            # Vector needs boost to compare with BM25.
            
            final_score = (adjusted_text_score * 0.7) + (vector_score * 5.0 * 0.3) + (effective_pr_score * 0.15)
            
            scores.append({
                'doc_id': doc_id,
                'score': final_score,
                'metadata': self.indexer.doc_metadata[doc_id],
                'components': {
                    'bm25': round(text_score, 3),
                    'vector': round(vector_score, 3),
                    'pr': round(norm_pr, 3),
                    'missing': missing_terms,
                    'phrase': phrase_bonus > 1.0
                }
            })
            
        # 6. Rank
        scores.sort(key=lambda x: x['score'], reverse=True)
        
        return scores, corrected_query, was_corrected

    def check_phrase_match(self, doc_id, query_phrase):
        """
        Check if the exact query phrase appears in the document text.
        """
        path = os.path.join(Config.STORAGE_PATH, 'raw', f"{doc_id}.html")
        try:
            with open(path, 'r', encoding='utf-8') as f:
                content = f.read()
            # Fast check on raw content or processed text?
            # Raw content might have tags, processed text (from clean_html) is better.
            _, _, text = self.processor.clean_html(content)
            return query_phrase in text.lower()
        except:
            return False

    def calculate_bm25(self, doc_id, query_tokens):
        score = 0
        k1 = 1.5
        b = 0.75
        
        doc_meta = self.indexer.doc_metadata[doc_id]
        doc_len = doc_meta['length']
        
        for term in query_tokens:
            if term not in self.indexer.index:
                continue
                
            # Get term frequency in this doc
            # This is O(N) lookup in list, could be O(1) if index was dict.
            # Optimization: Pre-convert postings to dict or iterate once?
            # For 200 pages, list iteration is instantaneous.
            tf = 0
            doc_list = self.indexer.index[term]
            for d_id, freq in doc_list:
                if d_id == doc_id:
                    tf = freq
                    break
            
            if tf == 0:
                continue
                
            # IDF
            # doc_freq = number of docs containing term
            doc_freq = len(doc_list)
            idf = math.log((self.doc_count - doc_freq + 0.5) / (doc_freq + 0.5) + 1)
            
            # BM25 term weight
            numerator = tf * (k1 + 1)
            denominator = tf + k1 * (1 - b + b * (doc_len / self.avg_dl))
            score += idf * (numerator / denominator)
            
        return score

    def get_snippet(self, doc_id, query):
        """
        Generate a snippet for the result.
        """
        # Load raw content
        path = os.path.join(Config.STORAGE_PATH, 'raw', f"{doc_id}.html")
        try:
            with open(path, 'r', encoding='utf-8') as f:
                content = f.read()
            title, text = self.processor.clean_html(content)
            
            # Simple snippet: Find best window of occurrence
            query_tokens = self.processor.tokenize(query)
            text_lower = text.lower()
            
            # Find all query term positions
            token_positions = []
            for term in query_tokens:
                start = 0
                while True:
                    pos = text_lower.find(term, start)
                    if pos == -1: break
                    token_positions.append(pos)
                    start = pos + len(term)
            
            token_positions.sort()
            
            if not token_positions:
                return text[:200] + "..."
                
            # Pick the window with most terms or just first occurence if sparse
            # Simple approach: Start from first term found
            best_pos = token_positions[0]
            
            # Try to start a bit before
            start = max(0, best_pos - 60)
            end = min(len(text), start + 240)
            
            snippet = text[start:end].replace('\n', ' ')
            
            # Bold terms (in HTML) - or leave to frontend?
            # Let's just return text for now, maybe add ...
            if start > 0: snippet = "..." + snippet
            if end < len(text): snippet = snippet + "..."
            
            return snippet
        except Exception:
            return "Preview unavailable"
