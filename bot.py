from flask import Flask, request
import telebot
import requests
from bs4 import BeautifulSoup
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import os

BOT_TOKEN = '7205848165:AAFueVRtFLGHtTExyoPpHV5b44IoSszOiPg'
bot = telebot.TeleBot(BOT_TOKEN)
server = Flask(__name__)

# Dicionário para armazenar links dos animes
anime_links = {}

# Comando para pesquisar animes
@bot.message_handler(commands=['p'])
def search_anime(message):
    anime_name = message.text[len('/p '):].strip().lower()
    if anime_name:
        search_url = f'https://animefire.plus/pesquisar/{anime_name.replace(" ", "%20")}'
        response = requests.get(search_url)
        if response.status_code != 200:
            bot.send_message(message.chat.id, "Erro ao acessar o site. Tente novamente mais tarde.")
            return

        soup = BeautifulSoup(response.content, 'html.parser')
        animes = soup.find_all('article', class_='cardUltimosEps')

        if animes:
            markup = InlineKeyboardMarkup()
            for index, anime in enumerate(animes):
                title = anime.find('h3', class_='animeTitle').text.strip()
                link = anime.find('a')['href']
                full_link = link if link.startswith('http') else f'https://animefire.plus{link}'

                anime_links[f"anime_{index}"] = full_link
                markup.add(InlineKeyboardButton(text=title, callback_data=f"anime_{index}"))

            bot.send_message(message.chat.id, "Animes encontrados:", reply_markup=markup)
        else:
            bot.send_message(message.chat.id, "Nenhum anime encontrado com esse nome.")
    else:
        bot.send_message(message.chat.id, "Por favor, forneça o nome do anime. Exemplo: /p boruto")

# Exibir detalhes do anime
@bot.callback_query_handler(func=lambda call: call.data.startswith('anime_'))
def anime_details(call):
    bot.delete_message(call.message.chat.id, call.message.message_id)

    anime_id = call.data
    if anime_id in anime_links:
        anime_url = anime_links[anime_id]
        response = requests.get(anime_url)
        if response.status_code != 200:
            bot.send_message(call.message.chat.id, "Erro ao acessar detalhes do anime.")
            return

        soup = BeautifulSoup(response.content, 'html.parser')
        title = soup.find('h1', class_='quicksand400').text.strip()
        synopsis_tag = soup.find('div', class_='divSinopse')
        synopsis_text = "Sinopse não disponível"
        if synopsis_tag:
            synopsis = synopsis_tag.find('span', class_='spanAnimeInfo')
            if synopsis:
                synopsis_text = synopsis.text.strip()
        
        truncated_synopsis = synopsis_text[:250] + '...' if len(synopsis_text) > 250 else synopsis_text
        image_tag = soup.find('div', class_='sub_animepage_img').find('img')
        image_url = image_tag['data-src'] if image_tag else None

        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton(text="Episódios", callback_data=f"episodes_{anime_id.split('_')[1]}"))

        bot.send_photo(
            call.message.chat.id,
            photo=image_url,
            caption=f"**{title}**\n\n{truncated_synopsis}",
            parse_mode='Markdown',
            reply_markup=markup
        )

# Webhook para receber atualizações
@server.route(f"/{BOT_TOKEN}", methods=['POST'])
def receive_update():
    json_data = request.get_json()
    bot.process_new_updates([telebot.types.Update.de_json(json_data)])
    return "OK", 200

# Rota para verificar se o bot está funcionando
@server.route("/", methods=['GET'])
def test():
    return "Bot está funcionando!", 200

# Iniciar o servidor
if __name__ == "__main__":
    server.run()
        
