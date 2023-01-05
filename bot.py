import telebot
import json
from datetime import datetime
from telebot import types
import redis
import re
import threading
from time import sleep


# Тут все переменные, дикты, листы которые используются в приложении.


reminderMessage = 'Время ответить за скед!!'
notYourDayReminder = 'Вообще ты мог сегодня не писать, но раз уж написал - ответь за скед!'

google_sheet = 'rand'

time_timer = 0
all_users = {}

list_with_days = ['Понедельник', 'Вторник', 'Среда', 'Четверг', 'Пятница', 'Суббота', 'Воскресенье']

list_with_hours = {"6 часов": 6, "10 часов": 10, "12 часов": 12}

pool = redis.ConnectionPool(host='127.0.0.1', port=6379, db=0)
redis = redis.Redis(connection_pool=pool)

# getting our bots TOKEN
bot = telebot.TeleBot('KEY')

keyWords = ['#sked']

how_to_use_message = "Для начала зарегайтесь командой <b>/register.</b>\n " \
                     "Потом настройте удобное вам время и дни недели командой <b>/settings</b>\n" \
                     "Дальше следует добавление ключевых слов, которые буду отслеживаться.\n" \
                     "#sked там уже есть. Для добавленя новых используйте команду <b>/keywords.</b>\n" \
                     "Для этого напишите\n<b>/keywords - слово, которое хотите добавить.</b>\n" \
                     "Вот и все. Бот настроен."

help_message = "Вот команды, которые вы можете использовать" \
               "\n\n" \
               "/start - включить бота\n" \
               "/help - открыть список всех команд\n" \
               "<b>/register - регистрация нового пользователя</b>\n" \
               "/how_to_use - как использовать бота\n" \
               "/settings - настройкм\n" \
               "/time - изменить время полученмя напоминалок\n" \
               "/keywords - добавить новое ключевое слово"

dic = []
list_with_mes_id = []


class Users:
    def __init__(self, day: list, time_t: int, chat: int, mes_with_sked: str):
        # self.user_id = user
        self.days = day
        self.time = time_t
        self.chat_id = chat
        self.mes = mes_with_sked

# start command


@bot.message_handler(commands=['start'])
def start(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    button = types.KeyboardButton("Привет!")
    markup.add(button)
    bot.send_message(message.chat.id, f'Привет. Я sked бот.', reply_markup=markup)


@bot.message_handler(commands=['sheet'])
def sheet(message):
    bot.send_message(message.chat.id, 'Отправьте ссылку на гугл таблицу')

# how to use bot


@bot.message_handler(commands=['how_to_use'])
def how_to_use(message):
    bot.send_message(message.chat.id, how_to_use_message, parse_mode='html')

# command to change settings


@bot.message_handler(commands=['settings'])
def settings(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    button1 = types.KeyboardButton("Время")
    button2 = types.KeyboardButton("Дни недели")
    button3 = types.KeyboardButton("Регистрация нового пользователя")
    markup.add(button1, button2, button3)
    bot.send_message(message.chat.id, f'Выбирайте, что хотите настроить.', reply_markup=markup)

# command to add yourself to users


@bot.message_handler(commands=['register'])
def register(message):

    list_days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']
    new_user = Users(list_days, 8, message.chat.id, 'smth')
    if message.from_user.id in all_users:
        bot.send_message(message.chat.id, "Вы уже зарегистрированы")
    else:
        all_users[message.from_user.id] = new_user
        bot.send_message(message.chat.id, "Вы успешно зарегистровались")

# setting time for schedule


@bot.message_handler(commands=['time'])
def time(message):

    if message.from_user.id in all_users.keys():
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        button1 = types.KeyboardButton("6 часов")
        button2 = types.KeyboardButton("10 часов")
        button3 = types.KeyboardButton("12 часов")
        markup.add(button1, button2, button3)
        time_mes = "Выбирайте удобное вам время после написания планнера."
        bot.send_message(message.chat.id, time_mes, reply_markup=markup)
    else:
        bot.send_message(message.chat.id, 'Вы не зарегистрированы')


@bot.message_handler(commands=['days'])
def days(message):

    if message.from_user.id in all_users.keys():
        all_users[message.from_user.id].days.clear()
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        button1 = types.KeyboardButton("Понедельник")
        button2 = types.KeyboardButton("Вторник")
        button3 = types.KeyboardButton("Среда")
        button4 = types.KeyboardButton("Четверг")
        button5 = types.KeyboardButton("Пятница")
        button6 = types.KeyboardButton("Суббота")
        button7 = types.KeyboardButton("Воскресенье")
        markup.add(button1, button2, button3, button4, button5, button6, button7)
        bot.send_message(message.chat.id, 'Выберите удобные вам дни', reply_markup=markup)
    else:
        bot.send_message(message.chat.id, 'Вы не зарегистрированы')

# send to user all commands he can use


@bot.message_handler(commands=['help'])
def helper(message):
    bot.send_message(message.chat.id, help_message, parse_mode='html')

# adding special words to search for


@bot.message_handler(commands=['keywords'])
def keyword(message):
    strnew = str(message.text).split()
    keyWords.append(strnew[1])
    bot.send_message(message.chat.id, f'Keyword {strnew[1]} was added', parse_mode='html')

# all cases when user sent text message


@bot.message_handler(content_types=['text'])
def just_text(message):

    if message.text == 'Привет!':
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        button1 = types.KeyboardButton(f'Хелп')
        button2 = types.KeyboardButton(f'Я знаю, что делать.')
        markup.add(button1, button2)
        bot.send_message(message.chat.id, f'Если не знаешь, что делать - нажми на кнопку.', reply_markup=markup)
    elif message.text == 'Хелп':
        bot.send_message(message.chat.id, help_message, parse_mode='html')
    elif message.text == "Я знаю, что делать.":
        bot.send_message(message.chat.id, 'Принято.', parse_mode='html')
    elif message.text == "Время":
        time_mes = "По умолчанию это 8 часов после написания планнера."
        bot.send_message(message.chat.id, time_mes, parse_mode='html')
        sleep(2)
        request_mes = "Вы хотите изменить время получения напоминалки?"
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        button1 = types.KeyboardButton("Да, я хочу изменить время")
        button2 = types.KeyboardButton("Нет, я не хочу изменить время")
        markup.add(button1, button2)
        bot.send_message(message.chat.id, request_mes, reply_markup=markup)
    elif message.text == "Да, я хочу изменить время":
        time_editing_mes = "Кликните на команду /time"
        bot.send_message(message.chat.id, time_editing_mes)
    elif message.text == "Нет, я не хочу изменить время":
        no_mes = "Хорошо. Бот будет отправлять вам напоминалки каждые 8 часов."
        bot.send_message(message.chat.id, no_mes, parse_mode='html')
    elif message.text == "Дни недели":
        day_mes = "По умолчанию это каждый рабочий день"
        bot.send_message(message.chat.id, day_mes, parse_mode='html')
        sleep(2)
        request_mes = "Вы хотите изменить дни недели получения напоминалок?"
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        button1 = types.KeyboardButton("Да, я хочу изменить дни.")
        button2 = types.KeyboardButton("Нет, я не хочу изменить дни.")
        markup.add(button1, button2)
        bot.send_message(message.chat.id, request_mes, reply_markup=markup)
    elif message.text == "Да, я хочу изменить дни.":
        bot.send_message(message.chat.id, 'Нажмите на команду /days', parse_mode='html')

    # TODO УБРАТЬ ПОЧТИ КОПИРОВАНИЕ И НАПОМНИТЬ РАССКАЗАТЬ

    elif message.text in list_with_days:
        if message.from_user.id in all_users.keys() and message.text:
            if message.text not in all_users[message.from_user.id].days:
                all_users[message.from_user.id].days.append(message.text)
                bot.send_message(message.chat.id, f'Вы успешно добавили {message.text}')
            else:
                bot.send_message(message.chat.id, f'У вас уже добавлен {message.text}')

    elif message.text == "Нет, я не хочу изменить дни.":
        no_mes = "Хорошо. Бот будет отправлять вам напоминалки каждый будний день."
        bot.send_message(message.chat.id, no_mes, parse_mode='html')
    elif message.text == "Регистрация нового пользователя":
        instruction_mes = "Кликните на команду /register."
        bot.send_message(message.chat.id, instruction_mes, parse_mode='html')

    elif message.text in list_with_hours.keys():
        if message.from_user.id in all_users.keys():
            hour = list_with_hours.get(message.text)
            all_users[message.from_user.id].time = hour
            bot.send_message(message.chat.id, f'Вы изменили время получения напоминалок на {message.text}')
            print(hour)

    elif message.text == f'https://docs.google.com/spreadsheets/d/{re.search("/d/(.*)/", message.text).group(1)}' \
                         f'{re.search("/edit(.*)", message.text).group(0)}':
        print(re.search("/d/(.*)", message.text).group(1))
        print(re.search("/edit(.*)", message.text).group(0))
        google_sheet = re.search("/d/(.*)", message.text).group(1)
        bot.send_message(message.chat.id, 'Вы добавили гугл таблицу')

    else:
        for i in message.text.split():
            for j in range(len(keyWords)):
                if i != keyWords[j]:
                    pass
                else:
                    if message.from_user.id in all_users.keys():
                        time_t = all_users[message.from_user.id].time * 3600
                        redis.setex(message.id, time_t, reminderMessage)
                        all_users[message.from_user.id].chat_id = message.chat.id
                        all_users[message.from_user.id].mes_with_sked = message
                        list_with_mes_id.append(message.id)
                        y = f"{message.chat.id}"
                        dic.append({y: message.text})
                        json_obj = json.dumps(dic, indent=2, ensure_ascii=False)
                        with open('bd.json', 'w') as outfile:
                            outfile.write(json_obj)
                        bot.reply_to(message, 'Добавлен!')
                    else:
                        bot.send_message(message.chat.id, "Вы не зарегистрированы")


def answer():
    while True:
        for user in all_users.keys():
            for mes_id in list_with_mes_id:
                if redis.ttl(mes_id) == -2:
                    list_with_mes_id.remove(mes_id)
                    if datetime.today().strftime(f"%A") in all_users[user].days:
                        bot.reply_to(all_users[user].mes_with_sked, reminderMessage)
                    else:
                        print(datetime.today().strftime("%A"))
                        bot.reply_to(all_users[user].mes_with_sked, notYourDayReminder)


thread_for_answering = threading.Thread(target=answer, args=(), daemon=True)
thread_for_answering.start()


# bot starting
bot.polling(none_stop=True)
