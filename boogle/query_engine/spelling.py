import os
import json
import collections
from boogle.config import Config

class SpellingCorrector:
    def __init__(self):
        self.vocabulary = {} # word -> count
        self.total_words = 0
        self.load_vocabulary()

    def load_vocabulary(self):
        path = os.path.join(Config.STORAGE_PATH, 'index', 'raw_vocabulary.json')
        if os.path.exists(path):
            with open(path, 'r') as f:
                self.vocabulary = json.load(f)
                self.total_words = sum(self.vocabulary.values())
        else:
            # Fallback to old vocabulary if new one missing (during migration)
            old_path = os.path.join(Config.STORAGE_PATH, 'index', 'vocabulary.json')
            if os.path.exists(old_path):
                with open(old_path, 'r') as f:
                    vocab_list = json.load(f)
                    self.vocabulary = {w: 1 for w in vocab_list}
                    self.total_words = len(vocab_list)
            else:
                print("Warning: No vocabulary found. Spelling correction disabled.")

    def P(self, word): 
        "Probability of `word`."
        N = self.total_words if self.total_words > 0 else 1
        return self.vocabulary.get(word, 0) / N

    def correction(self, word): 
        "Most probable spelling correction for word."
        if not self.vocabulary:
            return word
        if word in self.vocabulary:
            return word
        
        # Candidates: known edits distance 1, 2, or known word itself
        candidates = (self.known([word]) or self.known(self.edits1(word)) or self.known(self.edits2(word)) or [word])
        return max(candidates, key=self.P)

    def known(self, words): 
        "The subset of `words` that appear in the dictionary of WORDS."
        return set(w for w in words if w in self.vocabulary)

    def edits1(self, word):
        "All edits that are one edit away from `word`."
        letters    = 'abcdefghijklmnopqrstuvwxyz'
        splits     = [(word[:i], word[i:])    for i in range(len(word) + 1)]
        deletes    = [L + R[1:]               for L, R in splits if R]
        transposes = [L + R[1] + R[0] + R[2:] for L, R in splits if len(R)>1]
        replaces   = [L + c + R[1:]           for L, R in splits if R for c in letters]
        inserts    = [L + c + R               for L, R in splits for c in letters]
        return set(deletes + transposes + replaces + inserts)

    def edits2(self, word): 
        "All edits that are two edits away from `word`."
        return (e2 for e1 in self.edits1(word) for e2 in self.edits1(e1))
        
    SKIP_WORDS = {'hi', 'hello', 'hey', 'thanks', 'ok', 'okay', 'boogle', 'search'}

    def correct_query(self, query):
        """
        Returns (corrected_query, was_corrected)
        """
        if not self.vocabulary:
            return query, False
            
        words = query.lower().split()
        corrected_words = []
        was_corrected = False
        
        print(f"[SPELL] Processing query: '{query}'")
        
        for word in words:
            # Rule 1: Length check (Skip short words)
            if len(word) < 3:
                print(f"[SPELL] SKIP '{word}': Length < 3")
                corrected_words.append(word)
                continue
                
            # Rule 2: Reserved/Skip words
            if word in self.SKIP_WORDS:
                print(f"[SPELL] SKIP '{word}': Reserved word")
                corrected_words.append(word)
                continue
                
            # Rule 3: Valid Raw Word (Exact match in vocabulary)
            if word in self.vocabulary:
                print(f"[SPELL] SKIP '{word}': Valid raw word in vocabulary")
                corrected_words.append(word)
                continue
            
            # Rule 4: Alpha check
            if not word.isalpha():
                print(f"[SPELL] SKIP '{word}': Non-alphabetic")
                corrected_words.append(word)
                continue
                
            # Attempt Correction
            candidate = self.correction(word)
            
            if candidate != word:
                print(f"[SPELL] CORRECT '{word}' -> '{candidate}'")
                corrected_words.append(candidate)
                was_corrected = True
            else:
                print(f"[SPELL] SKIP '{word}': No correction found")
                corrected_words.append(word)
            
        return ' '.join(corrected_words), was_corrected
