import os
import telebot
from flask import Flask, request
import requests
from bs4 import BeautifulSoup
import psycopg2

# Configurações do Bot
API_TOKEN = os.getenv('6621058997:AAHbefc8qVjo_-kUDqF4lhBcauRZuO1K_Bo')  # Configurado no ambiente do Vercel
bot = telebot.TeleBot(API_TOKEN)

# Configuração do Banco de Dados
DATABASE_URL = os.getenv('DATABASE_URL')  # URL do banco PostgreSQL
conn = psycopg2.connect(DATABASE_URL, sslmode='require')
cursor = conn.cursor()

# Criar tabelas se não existirem
cursor.execute("""
    CREATE TABLE IF NOT EXISTS usuarios (
        id BIGINT PRIMARY KEY
    )
""")
cursor.execute("""
    CREATE TABLE IF NOT EXISTS episodios (
        id SERIAL PRIMARY KEY,
        link TEXT NOT NULL UNIQUE,
        titulo TEXT NOT NULL,
        episodio TEXT NOT NULL,
        imagem TEXT NOT NULL,
        enviado BOOLEAN DEFAULT FALSE
    )
""")
conn.commit()

# Funções para buscar animes e episódios
def search_animes(query):
    url = f'https://goyabu.to/?s={query}'
    try:
        response = requests.get(url)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            animes = []
            for item in soup.select("article.boxAN"):
                link = item.select_one("a")["href"]
                title = item.select_one("div.title").text
                image = item.select_one("img")["src"]
                animes.append({"link": link, "title": title, "image": image})
            return animes
    except Exception as e:
        print(f"Erro ao buscar animes: {e}")
    return []

def get_episodes(anime_url):
    try:
        response = requests.get(anime_url)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            episodes = []
            for item in soup.select("ul.listaEps li a"):
                link = item["href"]
                text = item.text.strip()
                episodes.append({"link": link, "text": text})
            return episodes
    except Exception as e:
        print(f"Erro ao buscar episódios: {e}")
    return []

def get_video_link(episode_url):
    try:
        response = requests.get(episode_url)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            video_links = []
            for iframe in soup.select("iframe.metaframe"):
                video_links.append(iframe["src"])
            return video_links
    except Exception as e:
        print(f"Erro ao buscar link de vídeo: {e}")
    return []

# Comandos do bot
@bot.message_handler(commands=['start'])
def start(message):
    cursor.execute("INSERT INTO usuarios (id) VALUES (%s) ON CONFLICT DO NOTHING", (message.from_user.id,))
    conn.commit()
    bot.send_message(message.chat.id, "✅ Você foi registrado! Use /EPS para ver episódios recentes ou /pesquisar para buscar animes.")

@bot.message_handler(commands=['EPS'])
def eps(message):
    cursor.execute("SELECT titulo, episodio, link FROM episodios ORDER BY id DESC LIMIT 10")
    episodes = cursor.fetchall()
    if episodes:
        for titulo, episodio, link in episodes:
            bot.send_message(message.chat.id, f"📺 {titulo} - {episodio}\n[Assista aqui]({link})", parse_mode='Markdown')
    else:
        bot.send_message(message.chat.id, "Nenhum episódio recente disponível.")

@bot.message_handler(commands=['pesquisar'])
def pesquisar(message):
    bot.send_message(message.chat.id, "Digite o nome do anime que deseja pesquisar:")
    bot.register_next_step_handler(message, handle_search)

def handle_search(message):
    query = message.text.strip()
    animes = search_animes(query)
    if animes:
        for anime in animes:
            bot.send_message(message.chat.id, f"📖 {anime['title']}\n[Link do Anime]({anime['link']})", parse_mode='Markdown')
    else:
        bot.send_message(message.chat.id, "Nenhum anime encontrado com esse nome.")

# Configuração do Webhook
app = Flask(__name__)

@app.route('/webhook', methods=['POST'])
def webhook():
    json_update = request.get_json()
    bot.process_new_updates([telebot.types.Update.de_json(json_update)])
    return "!", 200

@app.before_first_request
def setup_webhook():
    bot.remove_webhook()
    bot.set_webhook(url=f"https://{os.getenv('VERCEL_URL')}/webhook")

# Rota padrão para verificação
@app.route('/', methods=['GET'])
def index():
    return "Bot está funcionando!", 200
                
