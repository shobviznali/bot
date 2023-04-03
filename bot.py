import telebot
import json
from datetime import datetime
from telebot import types
import redis
import re
import threading
from time import sleep
import psycopg2
from config import host, user, password, db_name
import os


# Тут все переменные, дикты, листы которые используются в приложении.

reminderMessage = 'Время ответить за скед!!'
notYourDayReminder = 'Вообще ты мог сегодня не писать, но раз уж написал - ответь за скед!'

google_sheet = 'rand'

time_timer = 0
all_users = {}

list_with_days = ['Понедельник', 'Вторник', 'Среда', 'Четверг', 'Пятница', 'Суббота', 'Воскресенье']

list_with_hours = {"6 часов":    6, "10 часов": 10, "12 часов": 12}


pool = redis.ConnectionPool(host='127.0.0.1', port=6379, db=0)

redis = redis.Redis(connection_pool=pool)

# getting our bots TOKEN
bot = telebot.TeleBot('5681996034:AAFpFl2Lr4QucJF2GSgNfCFU19RE5xMR_zI')

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
dict_with_mes_id = {}


# connecting with datebase

try:
    connection = psycopg2.connect(
        host=host,
        user=user,
        password=password,
        database=db_name,
    )   

    connection.autocommit = True

    with connection.cursor() as cursor:
        cursor.execute(
            """CREATE TABLE users(
                id INTEGER not null PRIMARY KEY,
                time INTEGER
                );"""
        )

except Exception as ex:
    print("[INFO] Error while working with PostgreSQL", ex)


try:
    connection = psycopg2.connect(
        host=host,
        user=user,
        password=password,
        database=db_name,
    )   

    connection.autocommit = True

    with connection.cursor() as cursor:
        cursor.execute(
            """CREATE TABLE skeds(
                id INTEGER,        
                chat_id BIGINT, 
                mes_id BIGINT
                );"""
        )

except Exception as ex:
    print("[INFO] Error while working with PostgreSQL", ex)


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

@bot.message_handler(commands=['update_chat'])
def update_chat_id(message):
    
    try:
        with connection.cursor() as cursor:
            print(message.chat.id)
            cursor.execute(f"UPDATE users SET chat_id = {message.chat.id} WHERE id = {message.from_user.id}")
    except Exception as ex:
        print(ex)

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

    connection.autocommit = True
    # list_days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']
    try:
        with connection.cursor() as cursor:
            cursor.execute(
                f""" INSERT INTO users(id, time) VALUES
            ({message.from_user.id}, 8);"""
            )
            bot.send_message(message.chat.id, 'Вы успешно зарегистровались')
    except Exception as ex:
        bot.send_message(message.chat.id, 'Вы уже зарегистрированы')
        print(ex)

    
    
# setting time for schedule


@bot.message_handler(commands=['time'])
def time(message):
    try:
        with connection.cursor() as cursor:
            cursor.execute(f"""SELECT time FROM users where id = {message.from_user.id}""")     
            markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
            button1 = types.KeyboardButton("6 часов")
            button2 = types.KeyboardButton("10 часов")
            button3 = types.KeyboardButton("12 часов")
            markup.add(button1, button2, button3)
            time_mes = "Выбирайте удобное вам время после написания планнера."
            bot.send_message(message.chat.id, time_mes, reply_markup=markup)
    except Exception as ex:
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
        pass
        # if message.from_user.id in all_users.keys() and message.text:
        #     if message.text not in all_users[message.from_user.id].days:
        #         all_users[message.from_user.id].days.append(message.text)
        #         bot.send_message(message.chat.id, f'Вы успешно добавили {message.text}')
        #     else:
        #         bot.send_message(message.chat.id, f'У вас уже добавлен {message.text}')

    elif message.text == "Нет, я не хочу изменить дни.":
        no_mes = "Хорошо. Бот будет отправлять вам напоминалки каждый будний день."
        bot.send_message(message.chat.id, no_mes, parse_mode='html')
    elif message.text == "Регистрация нового пользователя":
        instruction_mes = "Кликните на команду /register."
        bot.send_message(message.chat.id, instruction_mes, parse_mode='html')

    elif message.text in list_with_hours.keys():
        with connection.cursor() as cursor:
            hour = list_with_hours.get(message.text)
            cursor.execute(f"""UPDATE users SET time = {hour} WHERE id = {message.from_user.id}""")
            bot.send_message(message.chat.id, f'Вы изменили время получения напоминалок на {message.text}')

    # elif message.text == f'https://docs.google.com/spreadsheets/d/{re.search("/d/(.*)/", message.text).group(1)}' \
    #                      f'{re.search("/edit(.*)", message.text).group(0)}':
    #     print(re.search("/d/(.*)", message.text).group(1))
    #     print(re.search("/edit(.*)", message.text).group(0))
    #     google_sheet = re.search("/d/(.*)", message.text).group(1)
    #     bot.send_message(message.chat.id, 'Вы добавили гугл таблицу')

    else:
        for i in message.text.split():
            for j in range(len(keyWords)):
                if i != keyWords[j]:
                    pass
                else:
                    # json_object = json.dumps(str(message), indent = 0)
                    connection.autocommit = True
                    time_t = 0
                    try:
                        with connection.cursor() as cursor:
                            cursor.execute(f"""INSERT INTO skeds (id, chat_id, mes_id) VALUES(
                            {message.from_user.id}, {message.chat.id}, {message.message_id})""")
                        with connection.cursor() as cursor2:
                            cursor2.execute(f"""SELECT time FROM users WHERE id = {message.from_user.id}""")
                            time_t = cursor2.fetchone()[0] * 3600
                            print(time_t)
                            redis.setex(message.message_id, time_t, message.from_user.id)
                            bot.send_message(message.chat.id, "Добавлен!")
                    except Exception as ex:
                            bot.send_message(message.chat.id, f'Вы не зарегистрированы {ex}')
                

#TODO NOT TODO BUT IT'S HERE

def answer():
    while True:
        skeds = set()
        for i in redis.scan_iter():
            skeds.add(i)
        for i in skeds:
            try:
                with connection.cursor() as cursor5:
                    cursor5.execute(f"""SELECT chat_id FROM skeds WHERE mes_id = {int(i)}""")
                    chat_id = cursor5.fetchone()[0]
                    if redis.exists(i):

                        pass
                    else:
                        bot.send_message(chat_id, 'blablalba', reply_to_message_id=int(i))
                        with connection.cursor() as cursor6:
                            cursor6.execute(f"""DELETE FROM skeds where mes_id = {int(i)}""")
            except Exception as ex:
                print(f'Вы не зарегистрированы {ex}')




thread_for_answering = threading.Thread(target=answer, args=(), daemon=True)
thread_for_answering.start()

bot.polling(none_stop=True)
