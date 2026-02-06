import os
import json
import time
from datetime import datetime, timedelta
from boogle.config import Config

class CrawlStateManager:
    def __init__(self):
        self.state_path = os.path.join(Config.STORAGE_PATH, 'crawl_state.json')
        self.state = {
            'total_pages_crawled': 0,
            'hourly_count': 0,
            'daily_count': 0,
            'last_reset_hour': time.time(),
            'last_reset_day': time.time()
        }
        self.load_state()

    def load_state(self):
        if os.path.exists(self.state_path):
            with open(self.state_path, 'r') as f:
                try:
                    self.state = json.load(f)
                except:
                    pass # Keep default if corrupted

    def save_state(self):
        with open(self.state_path, 'w') as f:
            json.dump(self.state, f)

    def _reset_counters_if_needed(self):
        now = time.time()
        
        # Hourly reset
        if now - self.state.get('last_reset_hour', 0) > 3600:
            self.state['hourly_count'] = 0
            self.state['last_reset_hour'] = now
            
        # Daily reset
        if now - self.state.get('last_reset_day', 0) > 86400:
            self.state['daily_count'] = 0
            self.state['last_reset_day'] = now
            
        self.save_state()

    def check_budget(self):
        """
        Returns (allowed: bool, wait_time: float)
        wait_time is in seconds.
        """
        self._reset_counters_if_needed()
        
        # Check Hourly
        if self.state['hourly_count'] >= Config.CRAWL_MAX_PAGES_PER_HOUR:
            # Calculate time until next hour reset
            wait = 3600 - (time.time() - self.state['last_reset_hour'])
            return False, max(1.0, wait)
            
        # Check Daily
        if self.state['daily_count'] >= Config.CRAWL_MAX_PAGES_PER_DAY:
            # Calculate time until next day reset
            wait = 86400 - (time.time() - self.state['last_reset_day'])
            return False, max(1.0, wait)
            
        # Check Storage (Approximate check)
        # TODO: Implement storage check via `du -sh` or walking dir
        # For now, assume OK
        
        return True, 0.0

    def increment_counters(self):
        self._reset_counters_if_needed()
        self.state['total_pages_crawled'] += 1
        self.state['hourly_count'] += 1
        self.state['daily_count'] += 1
        self.save_state()
