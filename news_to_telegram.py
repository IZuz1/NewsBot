import requests
import pytz
import re
from datetime import datetime
from dotenv import load_dotenv
import os

load_dotenv()

PERPLEXITY_API_KEY = os.getenv('PERPLEXITY_API_KEY')
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

class NewsBotFull:
    def __init__(self, perplexity_key, telegram_token, telegram_chat_id):
        self.perplexity_key = perplexity_key
        self.telegram_token = telegram_token
        self.telegram_chat_id = telegram_chat_id
        self.perplexity_url = "https://api.perplexity.ai/chat/completions"
        self.telegram_url = f"https://api.telegram.org/bot{self.telegram_token}/sendMessage"

    def get_news_from_perplexity(self, topic, search_recency="day"):
        headers = {
            "Authorization": f"Bearer {self.perplexity_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": "sonar",
            "messages": [
                {"role": "system", "content": "Ты помощник для сбора новостей, выдавай удобные списки."},
                {"role": "user", "content": f"Собери сводку по теме: {topic}. Покажи структурировано: разделы, пункты, источники."}
            ],
            "max_tokens": 800,
            "temperature": 0.2,
            "search_recency_filter": search_recency,
            "top_p": 0.9
        }
        resp = requests.post(self.perplexity_url, headers=headers, json=payload, timeout=60)
        resp.raise_for_status()
        return resp.json()['choices'][0]['message']['content']

    def parse_to_sections(self, text_block):
        """
        Разделяет текст Перплексити на секции типа:
        "⚔️🇺🇦 Конфликт России и Украины
        - фраза
        - фраза"
        Возвращает список блоков для форматтера
        """
        out = []
        sections = re.split(r'\n(?=\W{0,3}\s*[\w\W]{3,30}\n-)', text_block)
        for sec in sections:
            m = re.match(r'^([^\w]*)([^\n]+)\n(.+)', sec, re.DOTALL)
            if not m:
                continue
            emoji, title, items = m.groups()
            items = [i for i in items.split('\n') if i.strip().startswith('-')]
            out.append({
                "emoji": emoji.strip() if emoji else "",
                "title": title.strip(),
                "entries": items
            })
        return out

    def format_telegram_message(self, sections, channel_tag="@nyannews_summary"):
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
        data = {
            "chat_id": self.telegram_chat_id,
            "text": message,
            "parse_mode": "HTML",
            "disable_web_page_preview": True
        }
        resp = requests.post(self.telegram_url, data=data, timeout=10)
        resp.raise_for_status()
        return resp.json().get('ok')

def main():
    topic = "итоги дня в России и мире"
    bot = NewsBotFull(PERPLEXITY_API_KEY, TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID)
    raw_text = bot.get_news_from_perplexity(topic)
    sections = bot.parse_to_sections(raw_text)
    msg = bot.format_telegram_message(sections)
    bot.send_to_telegram(msg)

if __name__ == "__main__":
    main()
