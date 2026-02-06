import time
import urllib.robotparser
from urllib.parse import urlparse
from boogle.config import Config

class DomainPolicer:
    def __init__(self):
        self.robots_cache = {} # domain -> RobotFileParser
        self.last_access = {} # domain -> timestamp
        self.default_delay = Config.CRAWL_POLITENESS_DELAY
        
    def get_domain(self, url):
        return urlparse(url).netloc
        
    def can_fetch(self, url, user_agent="BoogleBot"):
        domain = self.get_domain(url)
        
        # Check Robots.txt
        if domain not in self.robots_cache:
            rp = urllib.robotparser.RobotFileParser()
            try:
                rp.set_url(f"http://{domain}/robots.txt")
                rp.read()
                self.robots_cache[domain] = rp
            except:
                # If robots.txt fails, assume allowed but be careful?
                # Or block? Standard is allow if no robots.txt
                # We'll create a dummy allowed one
                rp = urllib.robotparser.RobotFileParser()
                rp.allow_all = True
                self.robots_cache[domain] = rp
        
        rp = self.robots_cache[domain]
        if not rp.can_fetch(user_agent, url):
            return False, "Disallowed by robots.txt"
            
        # Check Delay
        last_time = self.last_access.get(domain, 0)
        now = time.time()
        
        # Prefer crawl-delay from robots.txt if available
        crawl_delay = rp.crawl_delay(user_agent)
        effective_delay = crawl_delay if crawl_delay else self.default_delay
        
        if now - last_time < effective_delay:
            wait_time = effective_delay - (now - last_time)
            return False, f"Rate limit. Wait {wait_time:.1f}s"
            
        return True, "OK"
        
    def record_access(self, url):
        domain = self.get_domain(url)
        self.last_access[domain] = time.time()
