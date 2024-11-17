import telebot
import requests
from bs4 import BeautifulSoup
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

# Substitua pelo seu Token do bot
BOT_TOKEN = '7205848165:AAFueVRtFLGHtTExyoPpHV5b44IoSszOiPg'
bot = telebot.TeleBot(BOT_TOKEN)

# Função para buscar os últimos episódios
@bot.message_handler(commands=['episodios'])
def get_latest_episodes(message):
    # URL do site
    url = 'https://animefire.plus/'

    # Envia uma requisição para o site
    response = requests.get(url)
    
    # Se a requisição falhar, avisa o usuário
    if response.status_code != 200:
        bot.send_message(message.chat.id, "Erro ao acessar o site. Tente novamente mais tarde.")
        return
    
    # Faz o parse do HTML com BeautifulSoup
    soup = BeautifulSoup(response.content, 'html.parser')

    # Seleciona os elementos que contêm os episódios
    item_elements = soup.select("div.col-12.col-sm-6.col-md-4.col-lg-6.col-xl-3.divCardUltimosEpsHome")

    # Cria uma lista para armazenar as informações dos episódios
    episodes = []

    # Loop para extrair as informações dos episódios
    for item in item_elements:
        titulo = item.select("h3.animeTitle")[0].text.strip()  # Título do anime
        link = item.select("a")[0]['href']  # Link para o anime
        capa = item.select("img.card-img-top.lazy.imgAnimesUltimosEps")[0]['data-src']  # Capa do anime
        episodio = item.select("span.numEp")[0].text.strip()  # Número do episódio

        # Adiciona as informações do episódio na lista
        episodes.append({
            'título': titulo,
            'link': link,
            'capa': capa,
            'episódio': episodio
        })

    # Se houver episódios, envia para o usuário
    if episodes:
        for episode in episodes:
            markup = InlineKeyboardMarkup()
            markup.add(InlineKeyboardButton(text="Assistir", url=episode['link']))
            
            bot.send_photo(
                message.chat.id,
                episode['capa'],
                caption=f"**{episode['título']}** - Episódio {episode['episódio']}\n{episode['link']}",
                reply_markup=markup
            )
    else:
        bot.send_message(message.chat.id, "Nenhum episódio recente encontrado.")

# Inicia o bot
if __name__ == "__main__":
    bot.polling(none_stop=True)
    
