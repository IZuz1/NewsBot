# Полный код для отправки новостей из Perplexity в Telegram канал
# Установка зависимостей: pip install requests schedule python-dotenv

import requests
import schedule
import time
import os
from datetime import datetime
from dotenv import load_dotenv

# Загружаем переменные из .env файла
load_dotenv()

# Ваши ключи и токены
PERPLEXITY_API_KEY = os.getenv('PERPLEXITY_API_KEY')  # или вставьте напрямую: "your_api_key_here"
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')  # или вставьте напрямую: "your_token_here"
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')      # или вставьте напрямую: "your_chat_id_here"

# Если используете вставку напрямую (не рекомендуется для production):
# PERPLEXITY_API_KEY = "ppl_your_api_key_here"
# TELEGRAM_BOT_TOKEN = "123456789:ABCDefGHIjklmnoPQRstuvWXYZ"
# TELEGRAM_CHAT_ID = "123456789"

class NewsBot:
    """Класс для управления сбором новостей и отправкой в Telegram"""

    def __init__(self, perplexity_key, telegram_token, telegram_chat_id):
        self.perplexity_key = perplexity_key
        self.telegram_token = telegram_token
        self.telegram_chat_id = telegram_chat_id
        self.perplexity_url = "https://api.perplexity.ai/chat/completions"
        self.telegram_url = f"https://api.telegram.org/bot{self.telegram_token}/sendMessage"

    def get_news_from_perplexity(self, topic, search_recency="day"):
        """
        Получает новости по заданной теме из Perplexity API
        - topic: тема для поиска новостей
        - search_recency: филь
