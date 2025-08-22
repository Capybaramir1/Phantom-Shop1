import telebot
import sqlite3
from telebot.types import ReplyKeyboardMarkup, KeyboardButton

TOKEN = "8202218400:AAG5fM1M_sKD6nnzEaXQAQQBdyMTlfZq_BE"
SELLERS = [6413382806]

bot = telebot.TeleBot(TOKEN)
conn = sqlite3.connect('loyalty.db', check_same_thread=False)
c = conn.cursor()
c.execute('''CREATE TABLE IF NOT EXISTS users (
    telegram_id TEXT PRIMARY KEY,
    password TEXT,
    points INTEGER,
    purchases TEXT
)''')
conn.commit()

def client_keyboard():
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add(KeyboardButton("/profile"), KeyboardButton("/order"))
    return keyboard

def seller_keyboard():
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add(KeyboardButton("/register"), KeyboardButton("/addpoints"), KeyboardButton("/discount"))
    return keyboard

@bot.message_handler(commands=['start'])
def start(message):
    if message.from_user.id in SELLERS:
        bot.reply_to(message, "Добро пожаловать, продавец!", reply_markup=seller_keyboard())
    else:
        bot.reply_to(message, "Добро пожаловать, клиент!", reply_markup=client_keyboard())

@bot.message_handler(commands=['register'])
def register(message):
    if message.from_user.id not in SELLERS:
        bot.reply_to(message, "Только продавцы могут регистрировать клиентов!")
        return
    try:
        args = message.text.split()[1:]
        if len(args) < 2:
            bot.reply_to(message, "Используйте: /register @username пароль")
            return
        username = args[0].replace('@', '')
        password = args[1]
        c.execute("INSERT OR REPLACE INTO users (telegram_id, password, points, purchases) VALUES (?, ?, ?, ?)",
                  (username, password, 0, ""))
        conn.commit()
        bot.reply_to(message, f"Клиент {username} зарегистрирован!")
        bot.send_message(message.chat.id, f"{username}, вы зарегистрированы! Используйте /profile пароль")
    except Exception as e:
        bot.reply_to(message, f"Ошибка: {e}")

@bot.message_handler(commands=['profile'])
def profile(message):
    try:
        args = message.text.split()[1:]
        if len(args) < 1:
            bot.reply_to(message, "Введите: /profile пароль")
            return
        password = args[0]
        c.execute("SELECT * FROM users WHERE telegram_id = ? AND password = ?",
                  (message.from_user.username, password))
        user = c.fetchone()
        if user:
            bot.reply_to(message, f"Ваш профиль:\nБаллы: {user[2]}\nПокупки: {user[3] or 'Нет покупок'}",
                         reply_markup=client_keyboard())
        else:
            bot.reply_to(message, "Неверный пароль или вы не зарегистрированы!")
    except Exception as e:
        bot.reply_to(message, f"Ошибка: {e}")

@bot.message_handler(commands=['order'])
def order(message):
    try:
        args = message.text.split(maxsplit=1)[1:]
        if not args:
            bot.reply_to(message, "Введите: /order товар доставка(дом/магазин)")
            return
        order_text = args[0]
        c.execute("UPDATE users SET purchases = purchases || ? WHERE telegram_id = ?",
                  (f"\n{order_text}", message.from_user.username))
        conn.commit()
        bot.reply_to(message, f"Заказ '{order_text}' принят! Ожидайте подтверждения.")
        for seller_id in SELLERS:
            bot.send_message(seller_id, f"Новый заказ от {message.from_user.username}: {order_text}")
    except Exception as e:
        bot.reply_to(message, f"Ошибка: {e}")

@bot.message_handler(commands=['addpoints'])
def addpoints(message):
    if message.from_user.id not in SELLERS:
        bot.reply_to(message, "Только продавцы могут начислять баллы!")
        return
    try:
        args = message.text.split()[1:]
        if len(args) < 2:
            bot.reply_to(message, "Используйте: /addpoints @username количество")
            return
        username = args[0].replace('@', '')
        points = int(args[1])
        c.execute("UPDATE users SET points = points + ? WHERE telegram_id = ?", (points, username))
        conn.commit()
        bot.reply_to(message, f"Добавлено {points} баллов для {username}")
        bot.send_message(message.chat.id, f"{username}, вам начислено {points} баллов!")
    except Exception as e:
        bot.reply_to(message, f"Ошибка: {e}")

@bot.message_handler(commands=['discount'])
def discount(message):
    if message.from_user.id not in SELLERS:
        bot.reply_to(message, "Только продавцы могут применять скидки!")
        return
    try:
        args = message.text.split()[1:]
        if len(args) < 3:
            bot.reply_to(message, "Используйте: /discount @username сумма процент")
            return
        username = args[0].replace('@', '')
        amount = float(args[1])
        percent = float(args[2])
        discount = amount * (percent / 100)
        points_needed = int(discount * 10)
        c.execute("SELECT points FROM users WHERE telegram_id = ?", (username,))
        user = c.fetchone()
        if user and user[0] >= points_needed:
            c.execute("UPDATE users SET points = points - ? WHERE telegram_id = ?",
                      (points_needed, username))
            conn.commit()
            bot.reply_to(message, f"Скидка {percent}% ({discount} руб) применена для {username}, списано {points_needed} баллов")
            bot.send_message(message.chat.id, f"{username}, вам применена скидка {percent}% на {amount} руб!")
        else:
            bot.reply_to(message, f"У {username} недостаточно баллов ({user[0] if user else 0}/{points_needed})")
    except Exception as e:
        bot.reply_to(message, f"Ошибка: {e}")

bot.polling()
