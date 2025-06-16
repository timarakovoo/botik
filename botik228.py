import osAdd commentMore actions
import random
import json
import requests
from io import BytesIO
from flask import Flask, request
import telebot
from telebot.types import Update

BOT_TOKEN = os.getenv("7798488343:AAHUeygP3dJLCy4ynNajG4tFfGurFhYDVPE")
WEBHOOK_URL = os.getenv("https://dashboard.render.com/project/prj-d17ke3ndiees7387kff0")

bot = telebot.TeleBot(BOT_TOKEN)
app = Flask(__name__)

DATA_FILE = "data.json"
user_collections = {}

# Загрузка данных
if os.path.exists(DATA_FILE):
    with open(DATA_FILE, "r") as f:
        user_collections = json.load(f)

# Сохранение данных
def save_data():
    with open(DATA_FILE, "w") as f:
        json.dump(user_collections, f)

def rarity_stars(rarity):
    return "⭐" * rarity

def generate_kitten():
    kitten_id = random.randint(100000, 999999)
    image_url = f"https://cataas.com/cat?width=300&height=300&uniq={kitten_id}"
    roll = random.randint(1, 100)
    rarity = 5 if roll <= 5 else 4 if roll <= 30 else 3
    return {"id": kitten_id, "url": image_url, "rarity": rarity}

def is_subscribed(user_id):
    try:
        member = bot.get_chat_member("@freekittens", user_id)
        return member.status in ['member', 'administrator', 'creator']
    except Exception as e:
        print(f"[Ошибка проверки подписки]: {e}")
        return False

@bot.message_handler(commands=['start', 'help'])
def start(message):
    welcome = (
        "👋 Привет! Я — казик котят, твой личный коллекционер вспатышей!\n\n"
        "📌 Доступные команды: (подпишись на @freekittens)\n"
        "🐱 /cat — получить случайного мягкого и всратого\n"
        "📖 /collection — посмотреть свою коллекцию\n"
        "🏆 /top — топ коллекционеров\n"
        "ℹ️ /help — список команд"
    )
    bot.send_message(message.chat.id, welcome)

@bot.message_handler(commands=['cat'])
def send_cat(message):
    user_id = message.from_user.id
    if not is_subscribed(user_id):
        bot.send_message(message.chat.id, "📛 Подпишись на @freekittens, чтобы получать котят!")
        return

    kitten = generate_kitten()
    user_collections.setdefault(str(user_id), [])

    already_has = kitten["id"] in user_collections[str(user_id)]
    if not already_has:
        user_collections[str(user_id)].append(kitten["id"])
        save_data()

    caption = f"{rarity_stars(kitten['rarity'])} Котёнок №{kitten['id']}\n"
    caption += "Ты уже видел его!" if already_has else "Добавлен в твою коллекцию!"

    try:
        response = requests.get(kitten["url"])
        response.raise_for_status()
        photo = BytesIO(response.content)
        photo.name = "kitten.jpg"
        bot.send_photo(message.chat.id, photo, caption=caption)
    except Exception as e:
        print("Ошибка загрузки:", e)
        bot.send_message(message.chat.id, "😿 Не удалось загрузить котёнка. Попробуй позже.")

@bot.message_handler(commands=['collection'])
def collection(message):
    user_id = message.from_user.id
    if not is_subscribed(user_id):
        bot.send_message(message.chat.id, "📛 Подпишись на @freekittens, чтобы смотреть коллекцию!")
        return

    collection = user_collections.get(str(user_id), [])
    if not collection:
        bot.send_message(message.chat.id, "У тебя пока нет котят 😿 Напиши /cat, чтобы начать!")
        return

    response = f"🐾 У тебя {len(collection)} котят!\nКаждый с уникальным номером и редкостью."
    bot.send_message(message.chat.id, response)

@bot.message_handler(commands=['top'])
def top(message):
    if not user_collections:
        bot.send_message(message.chat.id, "Топ пока пуст 🫥")
        return

    sorted_top = sorted(user_collections.items(), key=lambda x: len(x[1]), reverse=True)
    text = "🏆 Топ коллекционеров:\n"
    for i, (uid, kittens) in enumerate(sorted_top[:5], start=1):
        try:
            user = bot.get_chat(int(uid))
            name = user.first_name or f"User {uid}"
        except:
            name = f"User {uid}"
        text += f"{i}. {name} — {len(kittens)} котят\n"

    bot.send_message(message.chat.id, text)

@bot.message_handler(commands=['broadcast'])
def broadcast_command(message):
    if message.from_user.username != "saygexteam":
        bot.reply_to(message, "⛔ У тебя нет прав.")
        return
    msg = bot.reply_to(message, "✏️ Введи сообщение для рассылки:")
    bot.register_next_step_handler(msg, send_broadcast)

def send_broadcast(message):
    if message.from_user.username != "saygexteam":
        return
    count = 0
    for uid in user_collections:
        try:
            bot.send_message(int(uid), f"📢 Сообщение от админа:\n{message.text}")
            count += 1
        except:
            continue
    bot.send_message(message.chat.id, f"✅ Отправлено {count} пользователям.")

# 🌐 Webhook обработка
@app.route('/', methods=['GET'])
def index():
    return "бот жив!"

@app.route(f'/{BOT_TOKEN}', methods=['POST'])
def webhook():
    update = Update.de_json(request.stream.read().decode("utf-8"))
    bot.process_new_updates([update])
    return "ok", 200

# 🎯 Установка вебхука
if __name__ == "__main__":
    bot.remove_webhook()
    bot.set_webhook(url=f"{WEBHOOK_URL}/{BOT_TOKEN}")
    app.run(host="0.0.0.0", port=int(os.environ.get('PORT', 5000)))
