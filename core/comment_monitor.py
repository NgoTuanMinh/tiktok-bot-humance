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
        if Config.COMMENT_ALREADY_OPEN:
            self.logger.info("Comment section is already open (flag set), skipping open attempt")
            return True
        # Kiểm tra thực tế xem comment section có hiển thị không (dự phòng)
        if self.human.is_comment_section_visible():
            self.logger.debug("Comment section already visible, no need to open")
            return True

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
        
        # Phát hiện chế độ
        is_search_mode = self.page.locator('[data-e2e="search-comment-container"]').is_visible(timeout=1000)
        if is_search_mode:
            self.logger.info("Search mode detected: using comment items from DivCommentItemContainer")
        else:
            self.logger.debug("Feed mode: using standard comment items")
        
        for scroll_idx in range(max_scrolls):
            if is_search_mode:
                # Trong search mode, comment nằm trong div class*="DivCommentItemContainer"
                # Nằm bên trong container [data-e2e="search-comment-container"]
                comment_items = self.page.locator('[data-e2e="search-comment-container"] div[class*="DivCommentItemContainer"]').all()
            else:
                comment_items = self.page.locator('[data-e2e="comment-item"], div[class*="DivCommentItemWrapper"]').all()
            
            current_count = len(comment_items)
            self.logger.debug(f"Scroll {scroll_idx+1}: found {current_count} comments")
            
            if current_count == last_comment_count:
                no_new += 1
                if no_new >= 3:
                    self.logger.info("No new comments after 3 scrolls, stopping")
                    break
            else:
                no_new = 0
                last_comment_count = current_count
                
                for idx, item in enumerate(comment_items):
                    try:
                        if is_search_mode:
                            # Lấy username từ a[data-e2e="comment-avatar-1"]
                            user_link = item.locator('a[data-e2e="comment-avatar-1"]').first
                            if not user_link.is_visible():
                                # Fallback: tìm link có chứa /@
                                user_link = item.locator('a[href*="/@"]').first
                            if not user_link.is_visible():
                                continue
                            href = user_link.get_attribute('href')
                            if href and '/@' in href:
                                username = href.split('/@')[-1].split('?')[0]
                            else:
                                continue
                            
                            # Lấy nội dung comment từ p[data-e2e="comment-level-1"]
                            text_elem = item.locator('p[data-e2e="comment-level-1"]').first
                            if not text_elem.is_visible():
                                # Fallback: lấy span bên trong
                                text_elem = item.locator('p[data-e2e="comment-level-1"] span').first
                            if text_elem.is_visible():
                                comment_text = text_elem.inner_text().strip()
                            else:
                                self.logger.debug(f"Could not extract comment text for @{username}")
                                continue
                        else:
                            # Feed mode (giữ nguyên logic cũ)
                            user_link = item.locator('a[href*="/@"]').first
                            if not user_link.is_visible():
                                continue
                            username = user_link.inner_text().lstrip('@')
                            text_elem = item.locator('[data-e2e="comment-text"], [data-e2e="comment-level-1"]').first
                            if text_elem.is_visible():
                                comment_text = text_elem.inner_text().strip()
                            else:
                                continue
                        
                        # Log nội dung comment (để debug)
                        self.logger.debug(f"Comment @{username}: {comment_text[:80]}")
                        
                        key = f"{username}_{comment_text[:50]}"
                        if key in self.processed_comments:
                            continue
                        self.processed_comments.add(key)
                        self.stats['comments_scanned'] += 1
                        
                        # Phát hiện cross-follow
                        if self.detect_cross_follow(comment_text):
                            self.logger.info(f"🎯 Cross-follow detected from @{username}: {comment_text[:60]}")
                            self.stats['cross_follow_detected'] += 1
                            
                            if username not in self.processed_users and Config.AUTO_FOLLOW_CROSS_FOLLOW:
                                # Kiểm tra giới hạn follow mỗi ngày
                                if self.stats['follows_done'] >= Config.MAX_FOLLOWS_PER_DAY:
                                    self.logger.info(f"Reached max follows per day ({Config.MAX_FOLLOWS_PER_DAY}), stopping further follows")
                                    # Không break vì có thể vẫn cần quét comment, nhưng không follow thêm
                                    # Nếu muốn dừng hẳn việc follow trong phiên này, có thể set flag
                                    continue
                                profile_url = f"https://www.tiktok.com/@{username}"
                                if self.human.follow_user_from_profile(profile_url):
                                    self.processed_users.add(username)
                                    self.stats['follows_done'] += 1
                                    self.logger.info(f"✅ Followed @{username}")
                                    
                                    if Config.AUTO_REPLY_TO_CROSS_FOLLOW and not is_search_mode:
                                        reply = random.choice(self.REPLY_TEMPLATES)
                                        if self.human.reply_to_comment(idx, reply):
                                            self.stats['replies_sent'] += 1
                                            self.logger.info(f"💬 Replied: {reply}")
                                            time.sleep(random.uniform(2, 4))
                                    elif Config.AUTO_REPLY_TO_CROSS_FOLLOW and is_search_mode:
                                        self.logger.warning("Reply not implemented in search mode (only follow)")
                    except Exception as e:
                        self.logger.debug(f"Error processing comment {idx}: {e}")
                        continue
            
            # Scroll để tải thêm comment
            if is_search_mode:
                container = self.page.locator('[data-e2e="search-comment-container"]').first
                if container.is_visible():
                    container.evaluate("el => el.scrollBy(0, 800)")
                else:
                    self.page.mouse.wheel(0, 800)
            else:
                self.human.scroll_comments(times=1)
            
            time.sleep(random.uniform(0.8, 1.5))
        
        self.logger.info(f"Finished scrolling. Total cross-follow processed: {total_processed}")
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
        try:
            if not self.open_comments_safely():
                self.logger.error("Could not open comments")
                return result
            self.scroll_and_process_comments(Config.MAX_COMMENT_SCROLLS)
            result.update({
                'success': True,
                'comments_scanned': self.stats['comments_scanned'],
                'cross_follow_found': self.stats['cross_follow_detected'],
                'follows_done': self.stats['follows_done'],
                'replies_sent': self.stats['replies_sent'],
                'captcha_encountered': self.stats['captcha_encountered']
            })
        except Exception as e:
            self.logger.error(f"Error in comment processing: {e}")
        finally:
            if not Config.KEEP_COMMENTS_OPEN:
                self.human.close_comments()
        return result