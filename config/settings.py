import os
from pathlib import Path
from dotenv import load_dotenv

env_path = Path(__file__).parent.parent / '.env'
load_dotenv(env_path)

class Config:
    # Sequential
    NUM_ACCOUNTS = int(os.getenv('NUM_ACCOUNTS', 1))
    SEQUENTIAL_MODE = os.getenv('SEQUENTIAL_MODE', 'true').lower() == 'true'
    BREAK_BETWEEN_ACCOUNTS = int(os.getenv('BREAK_BETWEEN_ACCOUNTS', 300))

    # Proxy
    USE_PROXY = os.getenv('USE_PROXY', 'false').lower() == 'true'
    PROXY_CONFIG_PATH = os.getenv('PROXY_CONFIG_PATH', 'config/proxies.yaml')

    # Session duration
    SESSION_DURATION_MINUTES = int(os.getenv('SESSION_DURATION_MINUTES', 30))

    # Watch time
    MIN_WATCH_TIME = int(os.getenv('MIN_WATCH_TIME', 5))
    MAX_WATCH_TIME = int(os.getenv('MAX_WATCH_TIME', 25))

    # Interaction rates
    LIKE_RATE = float(os.getenv('LIKE_RATE', 0.08))
    FOLLOW_RATE = float(os.getenv('FOLLOW_RATE', 0.01))
    SHARE_RATE = float(os.getenv('SHARE_RATE', 0.002))
    COMMENT_RATE = float(os.getenv('COMMENT_RATE', 0.08))

    # Scroll
    SCROLL_MIN = int(os.getenv('SCROLL_MIN', 200))
    SCROLL_MAX = int(os.getenv('SCROLL_MAX', 700))
    SCROLL_BACK_RATE = float(os.getenv('SCROLL_BACK_RATE', 0.08))
    SKIP_RATE = float(os.getenv('SKIP_RATE', 0.12))
    REWATCH_RATE = float(os.getenv('REWATCH_RATE', 0.10))

    # Limits
    MAX_LIKES_PER_HOUR = int(os.getenv('MAX_LIKES_PER_HOUR', 40))
    MAX_FOLLOWS_PER_DAY = int(os.getenv('MAX_FOLLOWS_PER_DAY', 15))
    MAX_ACTIONS_PER_MINUTE = int(os.getenv('MAX_ACTIONS_PER_MINUTE', 12))

    # Debug
    HEADLESS_MODE = False   # Chrome profile không hỗ trợ headless ổn định
    VERBOSE_LOG = os.getenv('VERBOSE_LOG', 'true').lower() == 'true'
    SAVE_SESSION = True     # Không dùng, giữ cho tương thích

    # Cross‑follow
    OPEN_COMMENTS_RATE = float(os.getenv('OPEN_COMMENTS_RATE', 0.08))
    MAX_COMMENTS_TO_SCAN = int(os.getenv('MAX_COMMENTS_TO_SCAN', 15))
    AUTO_REPLY_TO_CROSS_FOLLOW = os.getenv('AUTO_REPLY_TO_CROSS_FOLLOW', 'true').lower() == 'true'
    AUTO_FOLLOW_CROSS_FOLLOW = os.getenv('AUTO_FOLLOW_CROSS_FOLLOW', 'true').lower() == 'true'
    MAX_COMMENT_SCROLLS = int(os.getenv('MAX_COMMENT_SCROLLS', 30))

    SCROLL_MODE = os.getenv('SCROLL_MODE', 'scroll').lower()
    SCROLL_DISTANCE_MIN = int(os.getenv('SCROLL_DISTANCE_MIN', 800))
    SCROLL_DISTANCE_MAX = int(os.getenv('SCROLL_DISTANCE_MAX', 1200))

    KEEP_COMMENTS_OPEN = os.getenv('KEEP_COMMENTS_OPEN', 'true').lower() == 'true'
    COMMENT_ALREADY_OPEN = os.getenv('COMMENT_ALREADY_OPEN', 'false').lower() == 'true'
    AUTO_REPLY_TO_CROSS_FOLLOW = os.getenv('AUTO_REPLY_TO_CROSS_FOLLOW', 'false').lower() == 'true'

    @classmethod
    def get_strategy_weights(cls, strategy='normal'):
        strategies = {
            'conservative': {
                'watch_time_range': (10, 30),
                'scroll_speed': 'slow',
                'like_rate': cls.LIKE_RATE * 0.6,
                'follow_rate': cls.FOLLOW_RATE * 0.5,
                'actions_per_minute': 6,
                'skip_rate': cls.SKIP_RATE * 0.5,
            },
            'normal': {
                'watch_time_range': (cls.MIN_WATCH_TIME, cls.MAX_WATCH_TIME),
                'scroll_speed': 'normal',
                'like_rate': cls.LIKE_RATE,
                'follow_rate': cls.FOLLOW_RATE,
                'actions_per_minute': 10,
                'skip_rate': cls.SKIP_RATE,
            },
            'aggressive': {
                'watch_time_range': (3, 15),
                'scroll_speed': 'fast',
                'like_rate': cls.LIKE_RATE * 1.5,
                'follow_rate': cls.FOLLOW_RATE * 2,
                'actions_per_minute': 15,
                'skip_rate': cls.SKIP_RATE * 0.3,
            }
        }
        return strategies.get(strategy, strategies['normal'])