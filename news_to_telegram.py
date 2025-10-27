import requests
import schedule
import time
import os
import re
from datetime import datetime
from dotenv import load_dotenv
import pytz

# Загружаем переменные из .env файла
load_dotenv()

PERPLEXITY_API_KEY = os.getenv('PERPLEXITY_API_KEY')
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

class NewsBot:
    """Класс для управления сбором новостей и отправкой в Telegram"""

    def __init__(self, perplexity_key, telegram_token, telegram_chat_id):
        self.perplexity_key = perplexity_key
        self.telegram_token = telegram_token
        self.telegram_chat_id = telegram_chat_id
        self.perplexity_url = "https://api.perplexity.ai/chat/completions"
        self.telegram_url = f"https://api.telegram.org/bot{self.telegram_token}/sendMessage"

    def get_news_from_perplexity(self, topic, search_recency="day"):
        """Получает новости по заданной теме из Perplexity API."""
        try:
            headers = {
                "Authorization": f"Bearer {self.perplexity_key}",
                "Content-Type": "application/json"
            }
            payload = {
                "model": "sonar",
                "messages": [
                    {
                        "role": "system",
                        "content": "Ты помощник для сбора новостей. Предоставляй только актуальную информацию."
                    },
                    {
                        "role": "user",
                        "content": f"Какие главные новости сейчас в области: {topic}? Дай краткий обзор с ссылками."
                    }
                ],
                "max_tokens": 800,
                "temperature": 0.2,
                "search_recency_filter": search_recency,
                "top_p": 0.9
            }
            response = requests.post(self.perplexity_url, headers=headers, json=payload, timeout=45)
            response.raise_for_status()
            data = response.json()
            if 'choices' in data and len(data['choices']) > 0:
                content = data['choices'][0]['message']['content']
                sources = data.get('search_results', [])
                return {
                    'content': content,
                    'sources': sources,
                    'tokens_used': data.get('usage', {}).get('total_tokens', 0)
                }
            else:
                print(f"Ошибка Perplexity API: {data}")
                return None
        except requests.exceptions.RequestException as e:
            print(f"Ошибка при запросе к Perplexity: {str(e)}")
            return None
        except Exception as e:
            print(f"Неожиданная ошибка: {str(e)}")
            return None

    def format_telegram_message(self, topic, news_data):
        """
        Красивое форматирование для Telegram:
        - Шапка с темой, дата МСК
        - Все заголовки до : жирным (<b>)
        - Ключевые слова "Главное/Факт/Итог/Важно" — тоже жирным
        - Без * и markdown, только HTML
        """
        msk_tz = pytz.timezone('Europe/Moscow')
        timestamp = datetime.now(msk_tz).strftime("%d.%m.%Y %H:%M МСК")
        header = f"🟦 <b>{topic}</b>\n━━━━━━━━━━━━━━━\n"

        body_raw = news_data['content'].strip()
        # Все заголовки до :
        body = re.sub(r"(^|\n)([^:\n]{2,40}:)", r"\1<b>\2</b>", body_raw)
        # Основные ключевые слова
        body = re.sub(r"\b(Главное|Важно|Итог|Факт)\b", r"<b>\1</b>", body)
        # Все даты вида 27.10 или 27.10.2025
        body = re.sub(r"(\d{1,2}\.\d{1,2}(?:\.\d{2,4})?)", r"📅 \1", body)
        # Списки — из минусов
        body = re.sub(r"(?m)^- ", "— ", body)
        # Убрать * и ** и пустые строки подряд
        body = re.sub(r"\*+", "", body)
        body = re.sub(r"\n{3,}", "\n\n", body)
        body = body[:700] + ("..." if len(body) > 700 else "")
        links = ""
        if news_data['sources']:
            links = "🔗 " + " | ".join([
                f"<a href='{src.get('url', '#')}'><b>{src.get('title','Источник')[:24]}</b></a>"
                for src in news_data['sources'][:2]
            ]) + "\n"
        footer = f"\n━━━━━━━━━━━━━━━\n<i>{timestamp}</i>\n"
        return header + body.strip() + "\n" + links + footer

    def send_to_telegram(self, message):
        """Отправляет сообщение в Telegram канал. Возвращает: True если успешно, False если ошибка."""
        try:
            data = {
                "chat_id": self.telegram_chat_id,
                "text": message,
                "parse_mode": "HTML"
            }
            response = requests.post(self.telegram_url, data=data, timeout=10)
            response.raise_for_status()
            result = response.json()
            if result.get('ok'):
                print(f"✅ Сообщение успешно отправлено в Telegram")
                return True
            else:
                print(f"❌ Ошибка Telegram: {result.get('description', 'Неизвестная ошибка')}")
                return False
        except requests.exceptions.RequestException as e:
            print(f"❌ Ошибка при отправке в Telegram: {str(e)}")
            return False
        except Exception as e:
            print(f"❌ Неожиданная ошибка: {str(e)}")
            return False

    def send_news(self, topic):
        """Основная функция - собирает новости и отправляет в Telegram."""
        print(f"🔍 Ищем новости по теме: {topic}")
        news_data = self.get_news_from_perplexity(topic, search_recency="day")
        if news_data is None:
            print("❌ Не удалось получить новости")
            return False
        message = self.format_telegram_message(topic, news_data)
        success = self.send_to_telegram(message)
        if success:
            print(f"✅ Новости успешно опубликованы")
        return success

    def schedule_news(self, topic, time_str):
        """Планирует отправку новостей по расписанию."""
        schedule.every().day.at(time_str).do(self.send_news, topic=topic)
        print(f"📅 Расписание установлено: {topic} - каждый день в {time_str}")

    def run_scheduler(self):
        """Запускает планировщик в бесконечном цикле"""
        print("🤖 Планировщик запущен. Нажмите Ctrl+C для остановки")
        try:
            while True:
                schedule.run_pending()
                time.sleep(60)
        except KeyboardInterrupt:
            print("\n⛔ Планировщик остановлен")

# ============== Примеры использования ==============

def example_single_news():
    bot = NewsBot(PERPLEXITY_API_KEY, TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID)
    bot.send_news("политическая ситуация в ДНР и ЛНР")

def example_scheduled_news():
    bot = NewsBot(PERPLEXITY_API_KEY, TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID)
    # bot.schedule_news("политика ДНР", "10:00")
    # bot.schedule_news("события Украины", "14:00")
    # bot.schedule_news("экономика", "18:00")
    bot.run_scheduler()

def example_multiple_topics():
    bot = NewsBot(PERPLEXITY_API_KEY, TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID)
    topics = [
        "политическая ситуация в ДНР",
        "события в Луганской области",
        "социальная политика на подконтрольных территориях"
    ]
    for topic in topics:
        print(f"\n{'='*50}")
        bot.send_news(topic)
        time.sleep(2)

if __name__ == "__main__":
    if not PERPLEXITY_API_KEY or not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("❌ Ошибка: Не установлены необходимые переменные окружения!")
        print("Установите в .env файле:")
        print("  PERPLEXITY_API_KEY=your_key_here")
        print("  TELEGRAM_BOT_TOKEN=your_token_here")
        print("  TELEGRAM_CHAT_ID=your_chat_id_here")
        exit(1)
    print("🤖 NewsBot - Автоматическая отправка новостей в Telegram")
    print("\nВыберите режим:")
    print("1. Отправить новости один раз")
    print("2. Запустить планировщик (по расписанию)")
    print("3. Отправить по нескольким темам")
    choice = input("\nВаш выбор (1-3): ").strip()
    if choice == "1":
        example_single_news()
    elif choice == "2":
        example_scheduled_news()
    elif choice == "3":
        example_multiple_topics()
    else:
        print("❌ Неверный выбор")
