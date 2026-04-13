import random
import time
import math
from typing import Tuple, Optional, List
from playwright.sync_api import Page
from config.settings import Config
from utils.logger import get_logger
import logging

class HumanActions:
    def __init__(self, page: Page):
        self.page = page
        self.logger = logging.getLogger("human_actions")
        self.logger.setLevel(logging.DEBUG)
        if not self.logger.handlers:
            ch = logging.StreamHandler()
            ch.setLevel(logging.DEBUG)
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            ch.setFormatter(formatter)
            self.logger.addHandler(ch)
    # ---------- Mouse ----------
    @staticmethod
    def _bezier(t, p0, p1, p2, p3):
        return (1-t)**3 * p0 + 3*(1-t)**2 * t * p1 + 3*(1-t) * t**2 * p2 + t**3 * p3

    def move_to(self, x: int, y: int, duration: float = None, noise: int = 5):
        try:
            start_x, start_y = self.page.mouse.position()
        except:
            start_x, start_y = 500, 300
        x += random.randint(-noise, noise)
        y += random.randint(-noise, noise)
        distance = math.hypot(x - start_x, y - start_y)
        if duration is None:
            duration = min(1.2, max(0.2, distance / 800))
        cp1_x = start_x + (x - start_x) * 0.25 + random.randint(-50, 50)
        cp1_y = start_y + (y - start_y) * 0.25 + random.randint(-50, 50)
        cp2_x = start_x + (x - start_x) * 0.75 + random.randint(-50, 50)
        cp2_y = start_y + (y - start_y) * 0.75 + random.randint(-50, 50)
        steps = max(20, int(duration * 60))
        for i in range(steps + 1):
            t = i / steps
            cur_x = self._bezier(t, start_x, cp1_x, cp2_x, x)
            cur_y = self._bezier(t, start_y, cp1_y, cp2_y, y)
            self.page.mouse.move(cur_x, cur_y)
            time.sleep(duration / steps * random.uniform(0.8, 1.2))

    def click_at(self, x: int, y: int, double: bool = False):
        self.move_to(x, y)
        time.sleep(random.uniform(0.1, 0.3))
        if double:
            self.page.mouse.dblclick(x, y)
        else:
            self.page.mouse.click(x, y)
        time.sleep(random.uniform(0.2, 0.5))

    def click_element(self, selector: str, timeout: int = 5000) -> bool:
        try:
            elem = self.page.locator(selector).first
            if elem.is_visible(timeout=timeout):
                box = elem.bounding_box()
                if box:
                    self.click_at(box['x'] + box['width']/2, box['y'] + box['height']/2)
                    return True
        except:
            pass
        return False

    # ---------- Keyboard ----------
    def type_like_human(self, text: str, delay_range: Tuple[float, float] = (0.05, 0.2)):
        for ch in text:
            delay = random.uniform(*delay_range)
            if random.random() < 0.05:
                time.sleep(delay * 3)
            self.page.keyboard.type(ch, delay=delay)
            if random.random() < 0.03:
                time.sleep(random.uniform(0.3, 0.8))

    def press(self, key: str):
        self.page.keyboard.down(key)
        time.sleep(random.uniform(0.05, 0.15))
        self.page.keyboard.up(key)
        time.sleep(random.uniform(0.05, 0.2))

    # ---------- Scroll ----------
    def scroll_natural(self, distance: int = None, direction: str = 'down'):
        if distance is None:
            # Giá trị mặc định an toàn nếu không có Config
            distance = random.randint(900, 1300)
        steps = random.randint(10, 20)
        remaining = distance
        for _ in range(steps):
            step = remaining / (steps - _) * random.uniform(0.7, 1.3)
            step = min(step, remaining)
            self.page.mouse.wheel(0, step if direction == 'down' else -step)
            remaining -= step
            time.sleep(random.uniform(0.02, 0.08))
        # Không cần scroll ngược lại vì mục đích là chuyển video

    # ---------- TikTok specific ----------
    def watch_video(self, min_sec: int = 5, max_sec: int = 25):
        duration = random.uniform(min_sec, max_sec)
        start = time.time()
        last_move = start
        while time.time() - start < duration:
            if time.time() - last_move > random.uniform(3, 7):
                vp = self.page.viewport_size
                if vp:
                    x = random.randint(vp['width']//3, 2*vp['width']//3)
                    y = random.randint(vp['height']//3, 2*vp['height']//3)
                    self.move_to(x, y, duration=0.5)
                    last_move = time.time()
            time.sleep(random.uniform(0.5, 1.5))

    def _hover_video_center(self):
        """Di chuyển chuột vào trung tâm video để lộ các nút điều khiển"""
        vp = self.page.viewport_size
        if vp:
            x = vp['width'] // 2
            y = vp['height'] // 2
            self.move_to(x, y, duration=0.5)
            time.sleep(random.uniform(0.3, 0.6))


    def like(self) -> bool:
        """Like video"""
        self._hover_video_center()
        try:
            # Tìm button chứa span data-e2e="like-icon"
            btn = self.page.locator("xpath=//button[.//span[@data-e2e='like-icon']]").first
            if btn.is_visible(timeout=2000):
                box = btn.bounding_box()
                if box:
                    self.click_at(box['x'] + box['width']/2, box['y'] + box['height']/2)
                    return True
        except Exception as e:
            print(f"Like error: {e}")
        return False

    def open_comments(self) -> bool:
        """Mở comment section bằng cách click vào nút comment"""
        # Cách 1: Dùng XPath tìm button chứa span có data-e2e="comment-icon"
        try:
            btn = self.page.locator("xpath=//button[.//span[@data-e2e='comment-icon']]").first
            if btn.is_visible(timeout=2000):
                box = btn.bounding_box()
                if box:
                    self.click_at(box['x'] + box['width']/2, box['y'] + box['height']/2)
                    time.sleep(random.uniform(1, 2))
                    return True
        except Exception as e:
            print(f"[DEBUG] XPath selector failed: {e}")
        
        # Cách 2: Dùng CSS :has (nếu Playwright hỗ trợ)
        try:
            btn = self.page.locator("button:has(span[data-e2e='comment-icon'])").first
            if btn.is_visible(timeout=2000):
                box = btn.bounding_box()
                if box:
                    self.click_at(box['x'] + box['width']/2, box['y'] + box['height']/2)
                    time.sleep(random.uniform(1, 2))
                    return True
        except Exception as e:
            print(f"[DEBUG] CSS :has selector failed: {e}")
        
        # Fallback: tìm theo class đặc trưng của button
        try:
            btn = self.page.locator("button.css-1ydks0-7937d88b--ButtonActionItem").first
            if btn.is_visible(timeout=2000):
                box = btn.bounding_box()
                if box:
                    self.click_at(box['x'] + box['width']/2, box['y'] + box['height']/2)
                    time.sleep(random.uniform(1, 2))
                    return True
        except:
            pass
        
        print("[DEBUG] Could not find comment button")
        return False

    def close_comments(self):
        """Đóng comment section bằng nút X (ưu tiên) hoặc ESC (dự phòng)"""
        # Cách 1: Tìm nút đóng có aria-label="exit"
        try:
            close_btn = self.page.locator('button[aria-label="exit"]').first
            if close_btn.is_visible(timeout=2000):
                box = close_btn.bounding_box()
                if box:
                    self.click_at(box['x'] + box['width']/2, box['y'] + box['height']/2)
                    time.sleep(random.uniform(0.5, 1))
                    self.logger.debug("Closed comments via X button")
                    return
        except Exception as e:
            self.logger.debug(f"X button not found: {e}")
        
        # Cách 2: Dùng phím ESC (fallback)
        self.press('Escape')
        time.sleep(random.uniform(0.5, 1))
        self.logger.debug("Closed comments via ESC")

    def scroll_comments(self, times: int = 1):
        for _ in range(times):
            self.page.mouse.wheel(0, random.randint(300, 600))
            time.sleep(random.uniform(0.3, 0.8))

    def get_comment_text_and_author(self, index: int = 0) -> Tuple[Optional[str], Optional[str]]:
        try:
            items = self.page.locator('[data-e2e="comment-item"]').all()
            if index >= len(items):
                return None, None
            item = items[index]
            text_elem = item.locator('[data-e2e="comment-text"]').first
            user_elem = item.locator('a[href*="/@"]').first
            if text_elem.is_visible() and user_elem.is_visible():
                text = text_elem.inner_text().strip()
                username = user_elem.inner_text().lstrip('@')
                return text, username
        except:
            pass
        return None, None

    def reply_to_comment(self, comment_index: int, reply_text: str) -> bool:
        try:
            items = self.page.locator('[data-e2e="comment-item"]').all()
            if comment_index >= len(items):
                return False
            item = items[comment_index]
            reply_btn = item.locator('button[data-e2e="comment-reply"]').first
            if not reply_btn.is_visible():
                item.click()
                time.sleep(0.5)
                reply_btn = self.page.locator('button[data-e2e="comment-reply"]').first
            if reply_btn.is_visible():
                box = reply_btn.bounding_box()
                if box:
                    self.click_at(box['x'] + box['width']/2, box['y'] + box['height']/2)
                    time.sleep(random.uniform(0.5, 1))
                    textarea = self.page.locator('textarea[placeholder*="Reply"]').first
                    if textarea.is_visible():
                        box = textarea.bounding_box()
                        if box:
                            self.click_at(box['x'] + box['width']/2, box['y'] + box['height']/2)
                            self.type_like_human(reply_text)
                            time.sleep(random.uniform(0.5, 1))
                            send_btn = self.page.locator('button[data-e2e="comment-post"]').first
                            if send_btn.is_visible():
                                box = send_btn.bounding_box()
                                if box:
                                    self.click_at(box['x'] + box['width']/2, box['y'] + box['height']/2)
                                    return True
        except:
            pass
        return False

    def is_comment_section_visible(self) -> bool:
        """Kiểm tra comment section có đang hiển thị không"""
        try:
            # Dựa trên HTML: section có class chứa 'CommentSidebarContainer' hoặc div comment-sidebar
            section = self.page.locator('section[class*="CommentSidebarContainer"], div[class*="comment-sidebar"], div[class*="DivCommentContainer"]').first
            return section.is_visible(timeout=1000)
        except:
            return False


    def click_next_arrow(self) -> bool:
        """Click nút mũi tên xuống (chuyển video tiếp theo)"""
        try:
            # Tìm container chứa nút điều hướng (thường là aside)
            container = self.page.locator('div[class*="FeedNavigationContainer"]').first
            if container.is_visible(timeout=2000):
                # Lấy tất cả button action-item trong container
                buttons = container.locator('button.action-item').all()
                if len(buttons) >= 2:
                    # Nút thứ hai (index 1) là nút xuống
                    down_btn = buttons[1]
                    if down_btn.is_visible():
                        box = down_btn.bounding_box()
                        if box:
                            self.click_at(box['x'] + box['width']/2, box['y'] + box['height']/2)
                            time.sleep(random.uniform(0.3, 0.6))
                            return True
        except Exception as e:
            print(f"click_next_arrow error: {e}")
        return False

    def click_prev_arrow(self) -> bool:
        """Click nút mũi tên lên (quay lại video trước)"""
        try:
            container = self.page.locator('div[class*="FeedNavigationContainer"]').first
            if container.is_visible(timeout=2000):
                buttons = container.locator('button.action-item').all()
                if len(buttons) >= 1:
                    up_btn = buttons[0]
                    # Chỉ click nếu nút không bị disabled (khi không ở đầu feed)
                    if up_btn.is_visible() and up_btn.get_attribute('disabled') is None:
                        box = up_btn.bounding_box()
                        if box:
                            self.click_at(box['x'] + box['width']/2, box['y'] + box['height']/2)
                            time.sleep(random.uniform(0.3, 0.6))
                            return True
        except Exception as e:
            print(f"click_prev_arrow error: {e}")
        return False

    def follow_user_from_profile(self, profile_url: str) -> bool:
        """Vào profile, kiểm tra follow/follower < 500, nếu đủ thì follow"""
        with self.page.context.expect_page() as new_page_info:
            self.page.evaluate(f"window.open('{profile_url}')")
        profile_page = new_page_info.value
        time.sleep(random.uniform(3, 6))
        
        # Lấy số following và followers
        try:
            following_elem = profile_page.locator('[data-e2e="following-count"]').first
            followers_elem = profile_page.locator('[data-e2e="followers-count"]').first
            if following_elem.is_visible() and followers_elem.is_visible():
                following_text = following_elem.inner_text().strip()
                followers_text = followers_elem.inner_text().strip()
                # Loại bỏ dấu phẩy (nếu có) và chuyển thành số
                following = int(following_text.replace(',', ''))
                followers = int(followers_text.replace(',', ''))
                self.logger.info(f"User stats: following={following}, followers={followers}")
                
                if following >= 500 or followers >= 500:
                    self.logger.info(f"Skipping follow: following={following} (>=500) or followers={followers} (>=500)")
                    time.sleep(random.uniform(2, 4))
                    profile_page.close()
                    return False
            else:
                self.logger.warning("Could not retrieve follow stats, skipping follow")
                time.sleep(random.uniform(2, 4))
                profile_page.close()
                return False
        except Exception as e:
            self.logger.error(f"Error reading follow stats: {e}")
            time.sleep(random.uniform(2, 4))
            profile_page.close()
            return False
        
        # Nếu đủ điều kiện, thực hiện follow
        human_profile = HumanActions(profile_page)
        selectors = [
            'button[data-e2e="follow-button"]',
            'button:has-text("Follow")',
            'button:has-text("Theo dõi")'
        ]
        for sel in selectors:
            try:
                btn = profile_page.locator(sel).first
                if btn.is_visible(timeout=2000):
                    btn_text = btn.inner_text().strip().lower()
                    if btn_text in ['follow', 'theo dõi']:
                        box = btn.bounding_box()
                        if box:
                            human_profile.click_at(box['x'] + box['width']/2, box['y'] + box['height']/2)
                            time.sleep(random.uniform(2, 4))
                            profile_page.close()
                            return True
                    else:
                        self.logger.debug(f"Button text is '{btn_text}', already following")
                        time.sleep(random.uniform(2, 4))
                        profile_page.close()
                        return False
            except Exception as e:
                self.logger.debug(f"Selector {sel} error: {e}")
                continue
        
        profile_page.close()
        return False