import re
import random
import time
from typing import Optional, Dict, List
from core.human_actions import HumanActions
from utils.logger import get_logger
from config.settings import Config

class RobustCommentMonitor:
    CROSS_FOLLOW_PATTERNS = [
        r'fl\s*chéo', r'chéo\s*fl', r'chéo', r'fl\s*cheo', r'cheo\s*fl',
        r'fl\s*lại', r'fl\s+rồi', r'đã\s*fl', r'fl\s*cho\s*mình',
        r'fl\s*đi', r'fl\s*nha', r'fl\s*nhé', r'cross\s*follow', r'follow\s*cross',
        r'🔁', r'🔄'
    ]
    REPLY_TEMPLATES = [
        "đã chéo", "chéo ạ", "Fl rồi chéo mình nha", "fl lại giúp mình nhé",
        "đã fl lại rồi nha", "chéo rồi ạ", "fl xong rồi, chéo lại mình nhé",
        "đã follow, chéo lại nha", "xong rồi đó", "fl lại mình với ạ",
        "đã chéo, cảm ơn bạn", "chéo thành công ạ"
    ]

    def __init__(self, page, account_id: str):
        self.page = page
        self.account_id = account_id
        self.logger = get_logger(f"{account_id}_comment")
        self.human = HumanActions(page)
        self.processed_comments = set()
        self.processed_users = set()
        self.stats = {
            'comments_scanned': 0,
            'cross_follow_detected': 0,
            'follows_done': 0,
            'replies_sent': 0,
            'captcha_encountered': False
        }

    def detect_cross_follow(self, text: str) -> bool:
        if not text:
            return False
        lower = text.lower()
        for pat in self.CROSS_FOLLOW_PATTERNS:
            if re.search(pat, lower):
                return True
        return False

    def open_comments_safely(self, max_retries=3):
        for _ in range(max_retries):
            if self.human.open_comments():
                time.sleep(1)
                return True
            time.sleep(2)
        return False

    def scroll_and_process_comments(self, max_scrolls=30):
        total_processed = 0
        last_comment_count = 0
        no_new = 0
        for _ in range(max_scrolls):
            items = self.page.locator('[data-e2e="comment-item"]').all()
            current_count = len(items)
            if current_count == last_comment_count:
                no_new += 1
                if no_new >= 3:
                    break
            else:
                no_new = 0
                last_comment_count = current_count
                # Xử lý các comment mới
                for idx, item in enumerate(items):
                    try:
                        text_elem = item.locator('[data-e2e="comment-text"]').first
                        user_elem = item.locator('a[href*="/@"]').first
                        if not text_elem.is_visible() or not user_elem.is_visible():
                            continue
                        comment_text = text_elem.inner_text().strip()
                        username = user_elem.inner_text().lstrip('@')
                        key = f"{username}_{comment_text[:50]}"
                        if key in self.processed_comments:
                            continue
                        self.processed_comments.add(key)
                        self.stats['comments_scanned'] += 1
                        if self.detect_cross_follow(comment_text):
                            self.stats['cross_follow_detected'] += 1
                            if username not in self.processed_users and Config.AUTO_FOLLOW_CROSS_FOLLOW:
                                self.logger.info(f"Cross-follow from @{username}")
                                profile_url = f"https://www.tiktok.com/@{username}"
                                if self.human.follow_user_from_profile(profile_url):
                                    self.processed_users.add(username)
                                    self.stats['follows_done'] += 1
                                    if Config.AUTO_REPLY_TO_CROSS_FOLLOW:
                                        reply = random.choice(self.REPLY_TEMPLATES)
                                        if self.human.reply_to_comment(idx, reply):
                                            self.stats['replies_sent'] += 1
                                            self.logger.info(f"Replied: {reply}")
                                            time.sleep(random.uniform(2, 4))
                    except:
                        continue
            self.human.scroll_comments(times=1)
            time.sleep(random.uniform(0.8, 1.5))
        return total_processed

    def process_all_comments_robust(self):
        result = {
            'success': False,
            'comments_scanned': 0,
            'cross_follow_found': 0,
            'follows_done': 0,
            'replies_sent': 0,
            'captcha_encountered': False
        }
        if not self.open_comments_safely():
            self.logger.error("Could not open comments")
            return result
        self.scroll_and_process_comments(Config.MAX_COMMENT_SCROLLS)
        self.human.close_comments()
        result.update({
            'success': True,
            'comments_scanned': self.stats['comments_scanned'],
            'cross_follow_found': self.stats['cross_follow_detected'],
            'follows_done': self.stats['follows_done'],
            'replies_sent': self.stats['replies_sent'],
            'captcha_encountered': self.stats['captcha_encountered']
        })
        return result