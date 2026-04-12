import random
import time
import math
from typing import Tuple, Optional, List
from playwright.sync_api import Page

class HumanActions:
    def __init__(self, page: Page):
        self.page = page

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
            distance = random.randint(300, 800)
        steps = random.randint(10, 20)
        remaining = distance
        for _ in range(steps):
            step = remaining / (steps - _) * random.uniform(0.7, 1.3)
            step = min(step, remaining)
            self.page.mouse.wheel(0, step if direction == 'down' else -step)
            remaining -= step
            time.sleep(random.uniform(0.02, 0.08))
        if random.random() < 0.1 and distance > 200:
            time.sleep(random.uniform(0.3, 0.8))
            back = random.randint(50, 150)
            self.page.mouse.wheel(0, -back if direction == 'down' else back)

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

    def like(self) -> bool:
        selectors = ['[data-e2e="like-icon"]', '[data-e2e="like"]', 'button[class*="LikeButton"]']
        for sel in selectors:
            if self.click_element(sel, timeout=2000):
                return True
        return False

    def open_comments(self) -> bool:
        selectors = ['[data-e2e="comment-icon"]', 'button[class*="CommentButton"]']
        for sel in selectors:
            if self.click_element(sel):
                time.sleep(random.uniform(1, 2))
                return True
        return False

    def close_comments(self):
        self.press('Escape')
        time.sleep(random.uniform(0.5, 1))

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

    def follow_user_from_profile(self, profile_url: str) -> bool:
        with self.page.context.expect_page() as new_page_info:
            self.page.evaluate(f"window.open('{profile_url}')")
        profile_page = new_page_info.value
        time.sleep(random.uniform(2, 3))
        human_profile = HumanActions(profile_page)
        selectors = ['[data-e2e="follow-button"]', 'button:has-text("Follow")']
        for sel in selectors:
            if human_profile.click_element(sel):
                time.sleep(1)
                profile_page.close()
                return True
        profile_page.close()
        return False