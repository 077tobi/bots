import sqlite3
import telebot
import requests
from bs4 import BeautifulSoup
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

# Configurações do Bot
API_TOKEN = '7205848165:AAFueVRtFLGHtTExyoPpHV5b44IoSszOiPg'  # Substitua pelo seu token
bot = telebot.TeleBot(API_TOKEN)

# Banco de dados
db_path = 'loja.db'
conn = sqlite3.connect(db_path, check_same_thread=False)
cursor = conn.cursor()

# Criação de tabelas
cursor.execute("""
    CREATE TABLE IF NOT EXISTS usuarios (
        id INTEGER PRIMARY KEY
    )
""")
cursor.execute("""
    CREATE TABLE IF NOT EXISTS episodios (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        link TEXT NOT NULL UNIQUE,
        titulo TEXT NOT NULL,
        episodio TEXT NOT NULL,
        imagem TEXT NOT NULL,
        enviado INTEGER DEFAULT 0
    )
""")
conn.commit()

# Função para buscar animes
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

# Função para buscar episódios de um anime
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

# **Função para pegar o link do vídeo de um episódio**
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

# Comando '/start'
@bot.message_handler(commands=['start'])
def start(message):
    cursor.execute("INSERT OR IGNORE INTO usuarios (id) VALUES (?)", (message.from_user.id,))
    conn.commit()
    bot.send_message(message.chat.id, "✅ Você foi registrado! Use /EPS para ver episódios recentes ou /pesquisar para buscar animes.")

# Comando '/EPS'
@bot.message_handler(commands=['EPS'])
def eps(message):
    episodes = cursor.execute("SELECT * FROM episodios ORDER BY id DESC").fetchall()
    if episodes:
        markup = InlineKeyboardMarkup()
        for episode in episodes[:10]:  # Limitar aos 10 mais recentes
            markup.add(InlineKeyboardButton(
                f"{episode[2]} - {episode[3]}", callback_data=f"select_episode_{episode[1]}"
            ))
        bot.send_message(message.chat.id, "📺 **Episódios Recentes:**", reply_markup=markup)
    else:
        bot.send_message(message.chat.id, "Nenhum episódio recente disponível.")

# Comando '/pesquisar'
@bot.message_handler(commands=['pesquisar'])
def pesquisar(message):
    bot.send_message(message.chat.id, "Digite o nome do anime que deseja pesquisar:")
    bot.register_next_step_handler(message, handle_search)

# Manipulador de pesquisa
def handle_search(message):
    query = message.text.strip()
    animes = search_animes(query)
    if animes:
        markup = InlineKeyboardMarkup()
        for anime in animes:
            markup.add(InlineKeyboardButton(anime['title'], callback_data=f"select_anime_{anime['link']}"))
        bot.send_message(message.chat.id, "📖 **Resultados da Pesquisa:**", reply_markup=markup)
    else:
        bot.send_message(message.chat.id, "Nenhum anime encontrado com esse nome.")

# Seleção de anime
@bot.callback_query_handler(func=lambda call: call.data.startswith("select_anime_"))
def select_anime(call):
    anime_url = call.data.split("_", 2)[2]
    episodes = get_episodes(anime_url)
    if episodes:
        markup = InlineKeyboardMarkup()
        for episode in episodes:
            markup.add(InlineKeyboardButton(episode['text'], callback_data=f"select_episode_{episode['link']}"))
        bot.edit_message_text("📺 **Episódios Disponíveis:**", call.message.chat.id, call.message.message_id, reply_markup=markup)
    else:
        bot.edit_message_text("Nenhum episódio encontrado para este anime.", call.message.chat.id, call.message.message_id)

# Seleção de episódio e obtenção do link de vídeo
@bot.callback_query_handler(func=lambda call: call.data.startswith("select_episode_"))
def select_episode(call):
    episode_url = call.data.split("_", 2)[2]
    video_links = get_video_link(episode_url)
    if video_links:
        for link in video_links:
            bot.send_message(call.message.chat.id, f"🎥 [Assista ao episódio aqui]({link})", parse_mode='Markdown')
    else:
        bot.send_message(call.message.chat.id, "Não foi possível encontrar links de vídeo para este episódio.")

# Rodar o bot
bot.polling(none_stop=True, interval=0)
