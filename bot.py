import os
from flask import Flask, request, jsonify
import requests
from bs4 import BeautifulSoup
import psycopg2
from psycopg2.extras import RealDictCursor
import telebot

# Configurações do Bot e Banco de Dados
API_TOKEN = os.getenv('BOT_TOKEN')  # Token do bot do Telegram
DATABASE_URL = os.getenv('DATABASE_URL')  # URL do banco PostgreSQL
bot = telebot.TeleBot(API_TOKEN)

# Configuração do Flask
app = Flask(__name__)

# Conexão com o Banco de Dados
conn = psycopg2.connect(DATABASE_URL, sslmode='require')
cursor = conn.cursor(cursor_factory=RealDictCursor)

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

# Funções auxiliares
def search_animes(query):
    """Busca animes no site Goyabu"""
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
    """Busca episódios de um anime"""
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
    """Obtém o link de vídeo de um episódio"""
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

# Rotas da API
@app.route('/webhook', methods=['POST'])
def webhook():
    """Recebe atualizações do Telegram via webhook"""
    json_update = request.get_json()
    bot.process_new_updates([telebot.types.Update.de_json(json_update)])
    return jsonify(success=True)

@app.route('/search', methods=['GET'])
def search():
    """Busca animes com base na consulta"""
    query = request.args.get('query', '')
    if not query:
        return jsonify({"error": "A consulta é obrigatória"}), 400
    animes = search_animes(query)
    return jsonify(animes)

@app.route('/episodes', methods=['GET'])
def episodes():
    """Busca episódios de um anime"""
    anime_url = request.args.get('anime_url', '')
    if not anime_url:
        return jsonify({"error": "A URL do anime é obrigatória"}), 400
    episodes = get_episodes(anime_url)
    return jsonify(episodes)

@app.route('/video', methods=['GET'])
def video():
    """Obtém o link do vídeo de um episódio"""
    episode_url = request.args.get('episode_url', '')
    if not episode_url:
        return jsonify({"error": "A URL do episódio é obrigatória"}), 400
    video_links = get_video_link(episode_url)
    return jsonify(video_links)

@app.route('/users', methods=['GET', 'POST'])
def users():
    """Gerencia usuários"""
    if request.method == 'POST':
        user_id = request.json.get('id')
        if not user_id:
            return jsonify({"error": "O ID do usuário é obrigatório"}), 400
        cursor.execute("INSERT INTO usuarios (id) VALUES (%s) ON CONFLICT DO NOTHING", (user_id,))
        conn.commit()
        return jsonify({"message": "Usuário registrado com sucesso"})
    else:
        cursor.execute("SELECT * FROM usuarios")
        users = cursor.fetchall()
        return jsonify(users)

@app.route('/episodes/recent', methods=['GET'])
def recent_episodes():
    """Retorna os episódios mais recentes"""
    cursor.execute("SELECT titulo, episodio, link FROM episodios ORDER BY id DESC LIMIT 10")
    episodes = cursor.fetchall()
    return jsonify(episodes)

@app.route('/', methods=['GET'])
def index():
    """Página inicial"""
    return "API do Bot Telegram está funcionando!", 200

# Configuração do webhook
@app.before_first_request
def setup_webhook():
    bot.remove_webhook()
    bot.set_webhook(url=f"https://{os.getenv('VERCEL_URL')}/webhook")

