import time
import requests
import json
import os
from datetime import datetime, timedelta, timezone
from dotenv import load_dotenv

# === Загрузка переменных из .env
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
CHECK_INTERVAL = 300
SENT_FILE = "sent_api.json"

TG_URL = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
LAYER3_API = "https://api.layer3.xyz/api/quest/filter"

# === Сохранённые квесты
if os.path.exists(SENT_FILE):
    with open(SENT_FILE, "r") as f:
        sent_links = set(json.load(f))
else:
    sent_links = set()

def save_sent():
    with open(SENT_FILE, "w") as f:
        json.dump(list(sent_links), f)

def send_to_telegram(text):
    try:
        response = requests.post(TG_URL, data={
            "chat_id": CHAT_ID,
            "text": text,
            "parse_mode": "HTML"
        })
        if response.status_code != 200:
            print("❌ Telegram Error:", response.text)
    except Exception as e:
        print("⚠️ Telegram Exception:", e)

def get_recent_quests():
    print("📡 Запрос к Layer3 API...")
    new_quests = []
    try:
        response = requests.get(LAYER3_API)
        data = response.json()
        now = datetime.now(timezone.utc)

        for quest in data.get("data", []):
            title = quest.get("title")
            slug = quest.get("slug")
            created_at = quest.get("createdAt")

            if not (title and slug and created_at):
                continue

            dt = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
            if now - dt > timedelta(hours=24):
                continue

            url = f"https://app.layer3.xyz/quest/{slug}"
            if url not in sent_links:
                new_quests.append((title, url))
    except Exception as e:
        print("❌ Ошибка API:", e)

    return new_quests

def monitor():
    while True:
        print("🔄 Проверка новых квестов...")
        quests = get_recent_quests()

        for title, url in quests:
            msg = f"🆕 Новый квест:\n<b>{title}</b>\n{url}"
            print(f"📤 Отправляю: {title}")
            send_to_telegram(msg)
            sent_links.add(url)

        if quests:
            save_sent()

        print(f"⏳ Ожидаем {CHECK_INTERVAL} сек...\n")
        time.sleep(CHECK_INTERVAL)

if __name__ == "__main__":
    monitor()
