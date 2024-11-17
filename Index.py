from flask import Flask, request
import telebot
import requests
from bs4 import BeautifulSoup
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import json

app = Flask(__name__)

BOT_TOKEN = '7205848165:AAFueVRtFLGHtTExyoPpHV5b44IoSszOiPg'
bot = telebot.TeleBot(BOT_TOKEN)

# Substitua seu código de bot normalmente aqui

@app.route('/' + BOT_TOKEN, methods=['POST'])
def webhook():
    json_str = request.get_data().decode('UTF-8')
    update = telebot.types.Update.de_json(json_str)
    bot.process_new_updates([update])
    return 'OK', 200

@app.route('/')
def index():
    return 'Bot is running!'

if __name__ == '__main__':
    bot.remove_webhook()
    bot.set_webhook(url='https://<your-vercel-app-url>/' + BOT_TOKEN)  # Defina a URL do seu webhook no Vercel
    app.run(host='0.0.0.0', port=5000)
    
