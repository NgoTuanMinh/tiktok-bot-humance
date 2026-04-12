import yaml
import time
from pathlib import Path
from bots.tiktok_bot import TikTokBot
from utils.logger import get_main_logger

class BotScheduler:
    def __init__(self):
        self.logger = get_main_logger()
        self.accounts = self._load_accounts()

    def _load_accounts(self):
        path = Path('config/accounts.yaml')
        if not path.exists():
            self.logger.error("accounts.yaml not found")
            return []
        with open(path, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
        accounts = [acc for acc in data.get('accounts', []) if acc.get('enabled')]
        self.logger.info(f"Loaded {len(accounts)} accounts")
        return accounts

    def run_sequential(self):
        for acc in self.accounts:
            self.logger.info(f"Starting account {acc['account_id']}")
            bot = TikTokBot(
                account_id=acc['account_id'],
                strategy=acc.get('strategy', 'normal'),
                proxy=None,   # có thể mở rộng
                user_data_dir=acc.get('user_data_dir'),
                profile_dir=acc.get('profile_dir')
            )
            try:
                if bot.start():
                    bot.run_session()
            except Exception as e:
                self.logger.error(f"Bot failed: {e}")
            finally:
                bot.browser_manager.close()
            time.sleep(30)  # nghỉ giữa các account
        self.logger.info("All accounts finished")

    def run(self):
        if self.accounts:
            self.run_sequential()