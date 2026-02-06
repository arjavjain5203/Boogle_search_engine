import time
import requests
import os
import hashlib
import json
import logging
from urllib.parse import urlparse, urljoin
from bs4 import BeautifulSoup
from boogle.config import Config
from boogle.crawler.state_manager import CrawlStateManager
from boogle.crawler.scheduler import CrawlScheduler
from boogle.crawler.politeness import DomainPolicer

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)

class BoundedCrawler:
    def __init__(self):
        Config.init_storage()
        
        self.state_manager = CrawlStateManager()
        self.scheduler = CrawlScheduler()
        self.policer = DomainPolicer()
        
        self.link_graph = {} # Basic in-memory graph, could be flushed to disk
        self.max_depth = Config.MAX_DEPTH
        self.max_pages = Config.MAX_PAGES
        
        # Load seeds if queue is empty
        if self.scheduler.size() == 0:
            logging.info("Queue empty. Loading seeds...")
            for url in Config.SEED_URLS:
                if self.is_valid_url(url):
                    self.scheduler.add_url(url, priority=1)

    def normalize_url(self, url):
        parsed = urlparse(url)
        # Keep path, strip fragment
        return f"{parsed.scheme}://{parsed.netloc}{parsed.path}"

    def get_domain(self, url):
        return urlparse(url).netloc

    def save_page(self, url, content):
        url_hash = hashlib.md5(url.encode()).hexdigest()
        filename = os.path.join(Config.STORAGE_PATH, 'raw', f"{url_hash}.html")
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(content)
        
        # Save metadata mapping (append/update)
        # TODO: Optimize this for scale (sqlite/key-value store)
        meta_path = os.path.join(Config.STORAGE_PATH, 'url_map.json')
        mapping = {}
        if os.path.exists(meta_path):
            try:
                with open(meta_path, 'r') as f:
                    mapping = json.load(f)
            except:
                pass
        
        mapping[url_hash] = url
        with open(meta_path, 'w') as f:
            json.dump(mapping, f, indent=2)

    def is_valid_url(self, url):
        parsed = urlparse(url)
        if not bool(parsed.netloc) or not bool(parsed.scheme):
            return False
            
        # Wikipedia Specific Filters
        if 'wikipedia.org' in parsed.netloc:
            path = parsed.path
            if not path.startswith('/wiki/'):
                return False
                
            forbidden_prefixes = [
                '/wiki/Wikipedia:', '/wiki/Special:', '/wiki/Help:', 
                '/wiki/Portal:', '/wiki/File:', '/wiki/Category:', 
                '/wiki/Template:', '/wiki/Template_talk:', '/wiki/Talk:',
                '/wiki/User:'
            ]
            for prefix in forbidden_prefixes:
                if path.startswith(prefix):
                    return False
            
            # Strict colon check
            if ':' in path[6:]:
                return False
                
        return True

    def run_continuous(self):
        logging.info("Starting Bounded Continuous Crawler...")
        print("Crawler started. Press Ctrl+C to stop.")
        
        while True:
            # 1. Budget Check
            allowed, wait_time = self.state_manager.check_budget()
            if not allowed:
                logging.warning(f"Budget exhausted. Sleeping for {wait_time:.1f}s...")
                time.sleep(wait_time)
                continue
                
            # 2. Get Next URL
            url, priority = self.scheduler.get_next_url()
            if not url:
                logging.info("Queue empty. Waiting for new seeds or restart...")
                time.sleep(10)
                continue
                
            # 3. Politeness Check
            can_fetch, reason = self.policer.can_fetch(url)
            if not can_fetch:
                logging.info(f"Skipping {url}: {reason}")
                # Re-add to queue with lower priority or delay?
                # For simplicity, if rate-limited, maybe push back with same priority but verify loop?
                # If "Disallowed", drop it. 
                # If "Rate limit", sleep or re-queue?
                # To prevent blocking the loop, we should probably re-queue it or sleep briefly if it's the only domain.
                # However, Scheduler blindly popped it.
                # Let's just sleep briefly if rate limited to allow progress, 
                # or better: simple sleep here since we are single-threaded.
                if "Rate limit" in reason:
                   time.sleep(0.5) # Mini wait
                   # Put back in queue? Or just drop to avoid stuck loop? 
                   # Let's drop for now or implementation gets complex with re-queuing delays.
                continue
            
            # 4. Fetch
            logging.info(f"Crawling: {url} (Priority: {priority})")
            try:
                self.policer.record_access(url)
                response = requests.get(url, timeout=10, headers={'User-Agent': 'BoogleBot/1.0'})
                
                if response.status_code == 200:
                    content = response.text
                    self.save_page(url, content)
                    self.state_manager.increment_counters()
                    
                    # 5. Extract Links
                    soup = BeautifulSoup(content, 'html.parser')
                    links_found = 0
                    
                    seed_domains = {self.get_domain(s) for s in Config.SEED_URLS}
                    
                    for a_tag in soup.find_all('a', href=True):
                        href = a_tag['href']
                        full_url = urljoin(url, href)
                        normalized = self.normalize_url(full_url)
                        
                        if self.is_valid_url(normalized):
                            # Stick to seed domains for now
                            if self.get_domain(normalized) in seed_domains:
                                self.scheduler.add_url(normalized, priority=10) # Standard priority
                                links_found += 1
                                
                    logging.info(f"Saved {url}. Found {links_found} links. Budget: {self.state_manager.state['hourly_count']}/{Config.CRAWL_MAX_PAGES_PER_HOUR}")
                    
                    # Save queue periodically
                    if self.state_manager.state['total_pages_crawled'] % 10 == 0:
                        self.scheduler.save_state()
                        
                else:
                    logging.warning(f"Failed to fetch {url}: Status {response.status_code}")
                    
            except Exception as e:
                logging.error(f"Error crawling {url}: {e}")

if __name__ == "__main__":
    crawler = BoundedCrawler()
    try:
        crawler.run_continuous()
    except KeyboardInterrupt:
        print("\nStopping crawler...")
        crawler.scheduler.save_state()
        print("State saved.")
