import telebot
import requests
from bs4 import BeautifulSoup
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import logging

# Configura o logging
logging.basicConfig(level=logging.DEBUG)

# Substitua pelo seu Token do bot
BOT_TOKEN = '7205848165:AAFueVRtFLGHtTExyoPpHV5b44IoSszOiPg'
bot = telebot.TeleBot(BOT_TOKEN)

# Função para buscar os últimos episódios
@bot.message_handler(commands=['episodios'])
def get_latest_episodes(message):
    # URL do site
    url = 'https://animefire.plus/'

    try:
        # Envia uma requisição para o site
        response = requests.get(url)
        
        # Checa se a requisição foi bem-sucedida
        if response.status_code != 200:
            bot.send_message(message.chat.id, f"Erro ao acessar o site. Status Code: {response.status_code}")
            return

        # Faz o parse do HTML com BeautifulSoup
        soup = BeautifulSoup(response.content, 'html.parser')

        # Seleciona os elementos que contêm os episódios
        item_elements = soup.select("div.col-12.col-sm-6.col-md-4.col-lg-6.col-xl-3.divCardUltimosEpsHome")

        if not item_elements:
            bot.send_message(message.chat.id, "Nenhum episódio encontrado.")
            return

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

        # Envia os episódios para o usuário
        for episode in episodes:
            markup = InlineKeyboardMarkup()
            markup.add(InlineKeyboardButton(text="Assistir", url=episode['link']))
            
            bot.send_photo(
                message.chat.id,
                episode['capa'],
                caption=f"**{episode['título']}** - Episódio {episode['episódio']}\n{episode['link']}",
                reply_markup=markup
            )
    
    except Exception as e:
        logging.error(f"Erro ao processar a requisição: {e}")
        bot.send_message(message.chat.id, "Houve um erro ao tentar buscar os episódios.")

# Inicia o bot
if __name__ == "__main__":
    bot.polling(none_stop=True)
        
