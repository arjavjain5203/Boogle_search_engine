import heapq
import os
import json
import time
from boogle.config import Config

class CrawlScheduler:
    def __init__(self):
        self.queue_path = os.path.join(Config.STORAGE_PATH, 'scheduler_queue.json')
        self.seen_path = os.path.join(Config.STORAGE_PATH, 'scheduler_seen.json')
        
        self.queue = [] # Min-heap [(priority, url), ...]
        self.seen = set() # Set of checked URLs to avoid cycles
        
        self.load_state()
        
    def add_url(self, url, priority=10):
        """
        Add URL to priority queue. Lower number = higher priority.
        Default priority 10.
        Seeds: 1
        High PR: 5
        Standard: 10
        """
        if url in self.seen:
            return
            
        heapq.heappush(self.queue, (priority, url))
        self.seen.add(url)
        # Periodically save? For now save on exit/loop
        
    def get_next_url(self):
        if not self.queue:
            return None, None
            
        priority, url = heapq.heappop(self.queue)
        return url, priority
        
    def save_state(self):
        # Flatten heap for JSON
        with open(self.queue_path, 'w') as f:
            json.dump(self.queue, f)
            
        with open(self.seen_path, 'w') as f:
            # Convert set to list
            json.dump(list(self.seen), f)
            
    def load_state(self):
        if os.path.exists(self.queue_path):
            try:
                with open(self.queue_path, 'r') as f:
                    # Convert list back to list (heapify not strictly needed if file order kept, but safe)
                    data = json.load(f)
                    self.queue = [tuple(x) for x in data]
                    heapq.heapify(self.queue)
            except:
                pass
                
        if os.path.exists(self.seen_path):
            try:
                with open(self.seen_path, 'r') as f:
                    self.seen = set(json.load(f))
            except:
                pass
                
    def size(self):
        return len(self.queue)
