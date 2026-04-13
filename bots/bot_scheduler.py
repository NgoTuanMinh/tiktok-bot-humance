import yaml
import time
from pathlib import Path
from bots.tiktok_bot import TikTokBot
from utils.logger import get_main_logger
from config.settings import Config

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
            bot = None
            try:
                bot = TikTokBot(
                    account_id=acc['account_id'],
                    strategy=acc.get('strategy', 'normal'),
                    proxy=None,
                    user_data_dir=acc.get('user_data_dir'),
                    profile_dir=acc.get('profile_dir')
                )
                if bot.start():
                    bot.run_session()
            except Exception as e:
                self.logger.error(f"Bot failed: {e}")
            finally:
                if bot and hasattr(bot, 'browser_manager'):
                    try:
                        bot.browser_manager.close()
                    except Exception as e:
                        self.logger.error(f"Error closing browser: {e}")
            time.sleep(Config.BREAK_BETWEEN_ACCOUNTS)
        self.logger.info("All accounts finished")

    def run(self):
        if self.accounts:
            self.run_sequential()