import requests
import schedule
import time
import os
import pytz
from datetime import datetime
from dotenv import load_dotenv

# Загружаем переменные из .env файла
load_dotenv()

PERPLEXITY_API_KEY = os.getenv('PERPLEXITY_API_KEY')
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

class NewsBot:
    """Класс для отправки готовых секций новостей в Telegram."""

    def __init__(self, telegram_token, telegram_chat_id):
        self.telegram_token = telegram_token
        self.telegram_chat_id = telegram_chat_id
        self.telegram_url = f"https://api.telegram.org/bot{self.telegram_token}/sendMessage"

    def format_telegram_message(self, sections, channel_tag="@nyannews_summary"):
        """
        sections — список: [{"emoji": "...", "title": "...", "entries": [строки]}]
        Формирует пост как на образце!
        """
        msk_tz = pytz.timezone('Europe/Moscow')
        timestamp = datetime.now(msk_tz).strftime("%d.%m.%Y %H:%M МСК")
        msg = ""
        for block in sections:
            msg += f"{block['emoji']} <b>{block['title']}</b>\n"
            for item in block['entries']:
                msg += f"{item}\n"
            msg += "\n"
        msg += f"<i>Канал с выжимками: {channel_tag}</i>\n"
        msg += f"<i>{timestamp}</i>"
        return msg

    def send_to_telegram(self, message):
        """Отправляет сообщение в Telegram."""
        try:
            data = {
                "chat_id": self.telegram_chat_id,
                "text": message,
                "parse_mode": "HTML",
                "disable_web_page_preview": True
            }
            response = requests.post(self.telegram_url, data=data, timeout=10)
            response.raise_for_status()
            result = response.json()
            if result.get('ok'):
                print("✅ Сообщение отправлено!")
                return True
            else:
                print(f"❌ Ошибка Telegram: {result.get('description', 'Неизвестная ошибка')}")
                return False
        except Exception as e:
            print(f"❌ Ошибка при отправке в Telegram: {str(e)}")
            return False

def demo():
    # Пример контента как на скриншоте
    sections = [
        {
            "emoji": "⚔️🇺🇦",
            "title": "Конфликт России и Украины",
            "entries": [
                "- Украинский дрон атаковал микроавтобус в Брянской области, погиб человек.",
                "- Лавров заявил о радикальной перемене позиции США по Украине.",
                "- Трамп прокомментировал испытания ракеты «Буревестник» в России.",
                "- Российские войска освободили несколько населенных пунктов в Украине."
            ]
        },
        {
            "emoji": "🇷🇺⚖️",
            "title": "Внутренние дела России",
            "entries": [
                "- В Петербурге задержаны подозреваемые в похищении предпринимателя.",
                "- Полиция закрыла майнинг-ферму в Ленобласти из-за кражи электроэнергии.",
                "- Суд Москвы заочно арестовал певицу Монеточку по делу об иноагентах.",
                "- Главреда «Важных историй» заочно приговорили к obligedительным работам."
            ]
        },
        {
            "emoji": "🌍🌐",
            "title": "Международные отношения",
            "entries": [
                "- Литва закрыла границу с Беларусью на неопределенный срок.",
                "- Итальянский суд постановил выдать Германию украинца Кузнецова.",
                "- Суд принял закон о денонсации соглашения с США по плутону.",
                "- Путин подписал закон о стратегическом партнерстве с Венесуэлой."
            ]
        }
    ]
    bot = NewsBot(TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID)
    msg = bot.format_telegram_message(sections)
    bot.send_to_telegram(msg)

if __name__ == "__main__":
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("❌ Не установлены TELEGRAM_BOT_TOKEN/CHAT_ID")
        exit(1)
    demo()
