import telebot
import random
import pickle
import os
import requests
from io import BytesIO

TOKEN = '7798488343:AAHUeygP3dJLCy4ynNajG4tFfGurFhYDVPE'  # 🔁 Замени на свой токен
bot = telebot.TeleBot(TOKEN)

DATA_FILE = "collections.pkl"

# 📂 Загрузка сохранённых коллекций
if os.path.exists(DATA_FILE):
    with open(DATA_FILE, "rb") as f:
        user_collections = pickle.load(f)
else:
    user_collections = {}


def save_data():
    with open(DATA_FILE, "wb") as f:
        pickle.dump(user_collections, f)


def rarity_stars(rarity):
    return "⭐" * rarity


# 🎲 Генерация нового котёнка
def generate_kitten():
    kitten_id = random.randint(100000, 999999)

    # Стабильный источник изображений
    image_url = f"https://cataas.com/cat?width=300&height=300&uniq={kitten_id}"

    # Шанс: 70% обычный, 25% редкий, 5% легендарный
    roll = random.randint(1, 100)
    if roll <= 5:
        rarity = 5
    elif roll <= 30:
        rarity = 4
    else:
        rarity = 3

    return {"id": kitten_id, "url": image_url, "rarity": rarity}


@bot.message_handler(commands=['спат'])
def start(message):
    welcome = (
        "👋 Привет! Я — казик котят, твой личный коллекционер вспатышей!\n\n"
        "📌 Доступные команды: (подпишись на @freekittens)\n"
        "🐱 /cat — получить случайного мягкого и всратого\n"
        "📖 /collection — посмотреть свою коллекцию\n"
        "🏆 /top — топ коллекционеров\n"
        "🏆 подпишись на @freekittens \n"
        "ℹ️ /help — список команд"
    )
    bot.send_message(message.chat.id, welcome)


@bot.message_handler(commands=['help'])
def help_command(message):
    start(message)

@bot.message_handler(commands=['broadcast'])
def broadcast_command(message):
    if message.from_user.username != "saygexteam":
        bot.reply_to(message, "⛔ У тебя нет прав использовать эту команду.")
        return

    msg = bot.reply_to(message, "✏️ Введи сообщение для рассылки всем пользователям:")
    bot.register_next_step_handler(msg, send_broadcast)


def send_broadcast(message):
    if message.from_user.username != "saygexteam":
        return

    broadcast_text = message.text
    count = 0
    failed = 0

    for user_id in user_collections:
        try:
            bot.send_message(user_id, f"📢 Сообщение от администратора:\n\n{broadcast_text}")
            count += 1
        except Exception as e:
            failed += 1
            print(f"[Не удалось отправить {user_id}]: {e}")

    bot.send_message(message.chat.id, f"✅ Сообщение отправлено {count} пользователям.\n❌ Ошибок: {failed}.")



@bot.message_handler(commands=['cat'])
def send_cat(message):
    user_id = message.from_user.id
    kitten = generate_kitten()

    if user_id not in user_collections:
        user_collections[user_id] = []

    already_has = kitten["id"] in user_collections[user_id]
    if not already_has:
        user_collections[user_id].append(kitten["id"])
        save_data()

    caption = f"{rarity_stars(kitten['rarity'])} Котёнок №{kitten['id']}\n"
    caption += "Ты уже видел его!" if already_has else "Добавлен в твою коллекцию!"

    # Скачиваем изображение и отправляем как файл
    try:
        response = requests.get(kitten["url"])
        response.raise_for_status()
        photo = BytesIO(response.content)
        photo.name = 'kitten.jpg'
        bot.send_photo(message.chat.id, photo=photo, caption=caption)
    except Exception as e:
        bot.send_message(message.chat.id, "😿 Не удалось загрузить котёнка. Попробуй ещё раз.")
        print("Ошибка загрузки:", e)


@bot.message_handler(commands=['collection'])
def collection(message):
    user_id = message.from_user.id
    collection = user_collections.get(user_id, [])

    if not collection:
        bot.reply_to(message, "У тебя пока нет котят 😿 Напиши /cat, чтобы начать собирать!")
        return

    response = f"🐾 У тебя {len(collection)} котят!\n"
    response += "Каждый с уникальным номером и редкостью."
    bot.reply_to(message, response)


@bot.message_handler(commands=['top'])
def top(message):
    if not user_collections:
        bot.reply_to(message, "Топ пока пуст 🫥")
        return

    top_list = sorted(user_collections.items(), key=lambda x: len(x[1]), reverse=True)
    text = ("🏆 Топ коллекционеров котят:\n"
            "😿 ( подпишись на @freekittens )😿\n"
            )
    for i, (uid, kittens_list) in enumerate(top_list[:5], start=1):
        try:
            user = bot.get_chat(uid)
            username = user.first_name or f"User {uid}"
        except:
            username = f"User {uid}"
        text += f"{i}. {username} — {len(kittens_list)} котят\n"

    bot.reply_to(message, text)


# 🚀 Запуск бота
print("Бот запущен.")
bot.polling()
