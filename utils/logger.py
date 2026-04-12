import logging
from pathlib import Path
from datetime import datetime

def get_logger(name: str):
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)
    if not logger.handlers:
        ch = logging.StreamHandler()
        ch.setLevel(logging.DEBUG)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        ch.setFormatter(formatter)
        logger.addHandler(ch)
        Path('data/logs').mkdir(parents=True, exist_ok=True)
        fh = logging.FileHandler(f'data/logs/{name}_{datetime.now():%Y%m%d}.log', encoding='utf-8')
        fh.setFormatter(formatter)
        logger.addHandler(fh)
    return logger

def get_main_logger():
    return get_logger('scheduler')