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

# Função para buscar episódios recentes diretamente do site https://goyabu.to/home-2
def get_recent_episodes():
    url = 'https://goyabu.to/home-2'
    try:
        response = requests.get(url)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            episodes = []
            for item in soup.select("article.boxEP"):
                link = item.select_one("a")["href"]
                title = item.select_one("div.title").text.strip()
                episode = item.select_one("div.titleEP").text.strip()
                image = item.select_one("img")["src"]
                episodes.append({
                    "link": link,
                    "title": title,
                    "episode": episode,
                    "image": image
                })
            return episodes
    except Exception as e:
        print(f"Erro ao buscar episódios recentes: {e}")
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
                episode_text = item.text.strip()
                episode_number = item.get("id", "").replace("ep_", "")
                episodes.append({
                    "link": link,
                    "episodeText": episode_text,
                    "episodeNumber": episode_number
                })
            return episodes
    except Exception as e:
        print(f"Erro ao buscar episódios: {e}")
    return []

# Enviar episódios recentes para todos os usuários
def send_recent_episodes():
    episodes = get_recent_episodes()
    if episodes:
        for episode in episodes:
            for usuario in cursor.execute("SELECT id FROM usuarios"):
                user_id = usuario[0]
                bot.send_message(user_id, f"Episódio novo disponível!\n\nTítulo: {episode['title']}\nEpisódio: {episode['episode']}\nLink: {episode['link']}")
    else:
        print("Nenhum episódio recente encontrado.")

# Comando '/start'
@bot.message_handler(commands=['start'])
def start(message):
    cursor.execute("INSERT OR IGNORE INTO usuarios (id) VALUES (?)", (message.from_user.id,))
    conn.commit()
    bot.send_message(message.chat.id, "✅ Você foi registrado! Use /EPS para ver episódios recentes ou /pesquisar para buscar animes.")

# Comando '/EPS'
@bot.message_handler(commands=['EPS'])
def eps(message):
    episodes = get_recent_episodes()
    if episodes:
        markup = InlineKeyboardMarkup()
        for episode in episodes[:10]:  # Limitar aos 10 episódios mais recentes
            markup.add(InlineKeyboardButton(
                f"{episode['title']} - Episódio {episode['episode']}", callback_data=f"select_episode_{episode['link']}"
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
                title = item.select_one("div.title").text.strip()
                image = item.select_one("img")["src"]
                animes.append({"link": link, "title": title, "image": image})
            return animes
    except Exception as e:
        print(f"Erro ao buscar animes: {e}")
    return []

# Seleção de anime e obtenção de episódios
@bot.callback_query_handler(func=lambda call: call.data.startswith("select_anime_"))
def select_anime(call):
    # Apagar botões anteriores para não acumular botões
    bot.edit_message_text(
        text="Carregando episódios...",
        chat_id=call.message.chat.id,
        message_id=call.message.message_id
    )
    
    anime_url = call.data.split("_", 2)[2]
    episodes = get_episodes(anime_url)
    
    if episodes:
        markup = InlineKeyboardMarkup()
        # Limitar a exibição de episódios (20 primeiros episódios)
        for episode in episodes[:20]:
            markup.add(InlineKeyboardButton(f"Episódio {episode['episodeNumber']} - {episode['episodeText']}", callback_data=f"select_episode_{episode['link']}"))
        bot.send_message(call.message.chat.id, "Escolha um episódio:", reply_markup=markup)
    else:
        bot.send_message(call.message.chat.id, "Nenhum episódio encontrado para este anime.")

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

# Função para pegar o link do vídeo de um episódio
def get_video_link(episode_url):
    try:
        response = requests.get(episode_url)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            video_links = []
            for iframe in soup.select("iframe.metaframe"):
                video_links.append(iframe
["src"])
            return video_links
    except Exception as e:
        print(f"Erro ao buscar link de vídeo: {e}")
    return []

# Rodar o bot
bot.polling(none_stop=True, interval=0)
