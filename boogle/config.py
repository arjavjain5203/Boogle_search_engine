import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SEED_URLS = os.getenv('SEED_URLS', '').split(',')
    MAX_DEPTH = int(os.getenv('MAX_DEPTH', 3))
    MAX_PAGES = int(os.getenv('MAX_PAGES', 200))
    STORAGE_PATH = os.getenv('STORAGE_PATH', './boogle/storage/data')
    RANKING_ALPHA = float(os.getenv('RANKING_ALPHA', 0.6))
    RANKING_BETA = float(os.getenv('RANKING_BETA', 0.4))
    TITLE_WEIGHT = float(os.getenv('TITLE_WEIGHT', 5.0))
    FLASK_PORT = int(os.getenv('FLASK_PORT', 5000))
    
    # Crawler Budgets
    CRAWL_MAX_PAGES_PER_HOUR = int(os.getenv('CRAWL_MAX_PAGES_PER_HOUR', 100))
    CRAWL_MAX_PAGES_PER_DAY = int(os.getenv('CRAWL_MAX_PAGES_PER_DAY', 1000))
    CRAWL_MAX_TOTAL_STORAGE_MB = int(os.getenv('CRAWL_MAX_TOTAL_STORAGE_MB', 500))
    CRAWL_POLITENESS_DELAY = float(os.getenv('CRAWL_POLITENESS_DELAY', 2.0))

    # Ensure storage directories exist
    @staticmethod
    def init_storage():
        os.makedirs(os.path.join(Config.STORAGE_PATH, 'raw'), exist_ok=True)
        os.makedirs(os.path.join(Config.STORAGE_PATH, 'index'), exist_ok=True)
