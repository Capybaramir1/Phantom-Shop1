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

@bot.message_handler(commands=['start'])
def start(message):
    if message.from_user.id in SELLERS:
        bot.reply_to(message, "Добро пожаловать, продавец!")
    else:
        bot.reply_to(message, "Добро пожаловать, клиент!")

@bot.message_handler(commands=['help'])
def help(message):
    bot.reply_to(message, "Используйте /start для начала.")

bot.polling()
