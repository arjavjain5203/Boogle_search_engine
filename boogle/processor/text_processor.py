import re
import string
from bs4 import BeautifulSoup
import nltk
from nltk.corpus import stopwords
from nltk.stem import PorterStemmer

class TextProcessor:
    def __init__(self):
        # Ensure NLTK data is downloaded
        try:
            nltk.data.find('corpora/stopwords')
        except LookupError:
            nltk.download('stopwords')
            
        self.stop_words = set(stopwords.words('english'))
        self.stemmer = PorterStemmer()
        
    def clean_html(self, html_content):
        """
        Remove boilerplate, scripts, styles, and extract main text.
        Returns tuple: (title, first_paragraph, body_text)
        """
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Remove script and style elements
        for script in soup(["script", "style", "meta", "noscript", "header", "footer", "nav", "aside"]):
            script.decompose()
            
        # Extract title
        title = soup.title.string if soup.title else "No Title"
        title = title.strip() if title else "No Title"
        
        # Extract First Paragraph (heuristic: first p tag with substantial text)
        first_para = ""
        for p in soup.find_all('p'):
            text = p.get_text().strip()
            if len(text) > 50: # Arbitrary threshold for "meaningful" paragraph
                first_para = text
                break
        
        # Get full text
        text = soup.get_text(separator=' ')
        
        # Clean up whitespace
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        text = '\n'.join(chunk for chunk in chunks if chunk)
        
        return title, first_para, text

    def tokenize(self, text, return_raw=False):
        """
        Normalize, tokenize, remove stop words, and stem.
        If return_raw is True, returns (stemmed_tokens, raw_words_before_stemming)
        """
        if not text:
            return [] if not return_raw else ([], [])
            
        # Lowercase
        text = text.lower()
        
        # Remove punctuation (replace with space to avoid merging words like "hello.world")
        text = re.sub(f'[{re.escape(string.punctuation)}]', ' ', text)
        
        # Tokenize by splitting on whitespace
        tokens = text.split()
        
        stemmed_tokens = []
        raw_words = []
        
        for word in tokens:
            if word not in self.stop_words and len(word) > 1 and word.isalnum():
                stemmed_tokens.append(self.stemmer.stem(word))
                raw_words.append(word)
        
        if return_raw:
            return stemmed_tokens, raw_words
        return stemmed_tokens

    def process_document(self, html_content):
        title, first_para, text = self.clean_html(html_content)
        
        # Tokenize title, first_para, and body separately
        # We also want raw words for the vocabulary building (from title and body)
        title_stemmed, title_raw = self.tokenize(title, return_raw=True)
        first_para_stemmed = self.tokenize(first_para)
        body_stemmed, body_raw = self.tokenize(text, return_raw=True)
        
        # Combined raw words for vocab
        raw_words = title_raw + body_raw
        
        return title, first_para, text, title_stemmed, first_para_stemmed, body_stemmed, raw_words
