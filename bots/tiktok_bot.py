import time
import random
from datetime import datetime, timedelta
from config.settings import Config
from core.browser_manager import BrowserManager
from core.human_actions import HumanActions
from core.comment_monitor import RobustCommentMonitor
from utils.logger import get_logger
from config.settings import Config

class TikTokBot:
    def __init__(self, account_id: str, strategy: str = 'normal', proxy: str = None,
                 user_data_dir: str = None, profile_dir: str = None):
        self.account_id = account_id
        self.strategy = strategy
        self.proxy = proxy
        self.user_data_dir = user_data_dir
        self.profile_dir = profile_dir
        self.logger = get_logger(account_id)
        self.browser_manager = BrowserManager(account_id, user_data_dir, profile_dir, proxy=proxy)
        self.page = None
        self.human = None
        self.comment_monitor = None
        self.stats = {
            'videos_watched': 0, 'likes': 0, 'follows': 0, 'shares': 0, 'scrolls': 0,
            'start_time': None, 'actions_this_hour': 0, 'last_hour_reset': None,
            'comments_scanned': 0, 'cross_follow_detected': 0,
            'cross_follow_follows': 0, 'cross_follow_replies': 0
        }
        self.weights = Config.get_strategy_weights(strategy)
        self._processing_comments = False

    def start(self):
        self.logger.info(f"🤖 Starting TikTok Bot for {self.account_id}")
        _, _, self.page = self.browser_manager.launch()
        self.human = HumanActions(self.page)
        self.comment_monitor = RobustCommentMonitor(self.page, self.account_id)
        if not self._ensure_login():
            raise Exception("Login failed")
        self.stats['start_time'] = datetime.now()
        self.stats['last_hour_reset'] = datetime.now()
        return True

    def _ensure_login(self):
        if 'login' in self.page.url.lower():
            self.logger.warning("Please login manually within 60 seconds...")
            for _ in range(60):
                time.sleep(1)
                if 'foryou' in self.page.url:
                    self.logger.info("Login success")
                    return True
            return False
        return True

    def run_session(self, duration_minutes=None):
        if not duration_minutes:
            duration_minutes = Config.SESSION_DURATION_MINUTES
        end_time = datetime.now() + timedelta(minutes=duration_minutes)
        self.logger.info(f"Running for {duration_minutes} minutes")
        while datetime.now() < end_time:
            if (datetime.now() - self.stats['last_hour_reset']).seconds >= 3600:
                self.stats['actions_this_hour'] = 0
                self.stats['last_hour_reset'] = datetime.now()
            if self.stats['actions_this_hour'] >= Config.MAX_ACTIONS_PER_MINUTE * 60:
                self.logger.warning("Hourly limit reached, waiting 5 min")
                time.sleep(300)
                continue
            self._perform_action()
            time.sleep(random.uniform(1.5, 4))
            if self.stats['actions_this_hour'] % 30 == 0 and self.stats['actions_this_hour'] > 0:
                self._show_stats()
        self._show_final_stats()

    def _perform_action(self):
        if self._processing_comments:
            return
        actions = [
            ('scroll', 0.60),
            ('watch', 0.20),
            ('like', self.weights['like_rate']),
            ('follow', self.weights['follow_rate']),
            ('share', Config.SHARE_RATE),
            ('open_comments', Config.COMMENT_RATE)
        ]
        actions = [(a, w) for a, w in actions if w > 0]
        action = random.choices([a[0] for a in actions], weights=[a[1] for a in actions])[0]

        if action == 'scroll':
            direction = random.choices(['down', 'up'], weights=[0.95, 0.05])[0]
            if Config.SCROLL_MODE == 'arrow':
                if direction == 'down':
                    success = self.human.click_next_arrow()
                else:
                    success = self.human.click_prev_arrow()
                if not success:
                    self.logger.debug("Arrow button not found, fallback to scroll")
                    distance = random.randint(Config.SCROLL_DISTANCE_MIN, Config.SCROLL_DISTANCE_MAX)
                    self.human.scroll_natural(distance=distance, direction=direction)
            else:
                distance = random.randint(Config.SCROLL_DISTANCE_MIN, Config.SCROLL_DISTANCE_MAX)
                self.human.scroll_natural(distance=distance, direction=direction)
            self.stats['scrolls'] += 1
        elif action == 'watch':
            self.human.watch_video(*self.weights['watch_time_range'])
            self.stats['videos_watched'] += 1
        elif action == 'like':
            if self.human.like():
                self.stats['likes'] += 1
        elif action == 'follow':
            if self.human.click_element('[data-e2e="follow-button"]'):
                self.stats['follows'] += 1
        elif action == 'share':
            if self.human.click_element('[data-e2e="share-icon"]'):
                self.stats['shares'] += 1
                time.sleep(1)
                self.human.press('Escape')
        elif action == 'open_comments':
            self._processing_comments = True
            try:
                result = self.comment_monitor.process_all_comments_robust()
                self.stats['comments_scanned'] += result['comments_scanned']
                self.stats['cross_follow_detected'] += result['cross_follow_found']
                self.stats['cross_follow_follows'] += result['follows_done']
                self.stats['cross_follow_replies'] += result['replies_sent']
                if result['captcha_encountered']:
                    self.logger.warning("CAPTCHA, pausing 60s")
                    time.sleep(60)
            finally:
                self._processing_comments = False
        self.stats['actions_this_hour'] += 1

    def _show_stats(self):
        elapsed = (datetime.now() - self.stats['start_time']).seconds // 60
        self.logger.info(f"[{elapsed}min] Videos: {self.stats['videos_watched']} | Likes: {self.stats['likes']} | Follows: {self.stats['follows']}")

    def _show_final_stats(self):
        self.logger.info("="*50)
        self.logger.info(f"FINAL STATS for {self.account_id}")
        self.logger.info(f"   Videos: {self.stats['videos_watched']}")
        self.logger.info(f"   Likes: {self.stats['likes']}")
        self.logger.info(f"   Follows: {self.stats['follows']}")
        self.logger.info(f"   Cross-follow detected: {self.stats['cross_follow_detected']}")
        self.logger.info(f"   Cross-follow follows: {self.stats['cross_follow_follows']}")
        self.logger.info(f"   Cross-follow replies: {self.stats['cross_follow_replies']}")
        self.logger.info("="*50)