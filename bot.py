from datetime import date
from telebot import types
import re
import threading
from time import sleep
import vars


# connecting with datebase

try:

    vars.connection.autocommit = True

    with vars.connection.cursor() as cursor:
        cursor.execute(
            """CREATE TABLE users(
                id BIGINT not null PRIMARY KEY,
                time INTEGER
                );"""
        )

except Exception as ex:
    print("[INFO] Error while working with PostgreSQL", ex)

try:


    with vars.connection.cursor() as cursor:
        cursor.execute(
            """CREATE TABLE skeds(
                id BIGINT,        
                chat_id BIGINT, 
                mes_id BIGINT
                );"""
        )

except Exception as ex:
    print("[INFO] Error while working with PostgreSQL", ex)


# start command


@vars.bot.message_handler(commands=['start'])
def start(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    button = types.KeyboardButton("Привет!")
    markup.add(button)
    vars.bot.send_message(message.chat.id, f'Привет. Я sked бот.', reply_markup=markup)


@vars.bot.message_handler(commands=['sheet'])
def sheet(message):
    vars.bot.send_message(message.chat.id, 'Отправьте ссылку на гугл таблицу')


# how to use bot


@vars.bot.message_handler(commands=['update_current'])
def update_current(message):

    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    vars.bot.send_message(message.chat.id, 'Через сколько вы хотите получить напоминание?', reply_markup=markup)

    button1 = types.KeyboardButton("Обнови на 5")
    button2 = types.KeyboardButton("Обнови на 6")
    button3 = types.KeyboardButton("Обнови на 7")
    button4 = types.KeyboardButton("Обнови на 8")
    button5 = types.KeyboardButton("Обнови на 9")
    button6 = types.KeyboardButton("Обнови на 10")
    markup.add(button1, button2, button3, button4, button5, button6)


@vars.bot.message_handler(commands=['how_to_use'])
def how_to_use(message):
    vars.bot.send_message(message.chat.id, vars.how_to_use_message, parse_mode='html')


# command to change settings

@vars.bot.message_handler(commands=['settings'])
def settings(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    button1 = types.KeyboardButton("Время")
    button2 = types.KeyboardButton("Дни недели")
    button3 = types.KeyboardButton("Регистрация нового поFreльзователя")
    markup.add(button1, button2, button3)
    vars.bot.send_message(message.chat.id, f'Выбирайте, что хотите настроить.', reply_markup=markup)



# command to add yourself to users


@vars.bot.message_handler(commands=['register'])
def register(message):
    # list_days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']
    try:

        with vars.connection.cursor() as cursor1:
            cursor1.execute(
                f""" INSERT INTO users(id, time) VALUES
            ({message.from_user.id}, 8);"""
            )
            if message.from_user.last_name is not None:
                identifier = message.from_user.first_name + '' + message.from_user.last_name
                vars.gs.add_username(identifier)
                vars.gs.add_id(message.from_user.id)
            else:
                vars.gs.add_id(message.from_user.id)
            vars.bot.send_message(message.chat.id, 'Вы успешно зарегистровались')
    except Exception as excep:
        vars.bot.send_message(message.chat.id, excep)
        print(excep)


# setting time for schedule


@vars.bot.message_handler(commands=['time'])
def time(message):
    try:
        vars.connection.autocommit = True
        with vars.connection.cursor() as cursor1:
            cursor1.execute(f"""SELECT time FROM users where id = {message.from_user.id}""")
            markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
            button1 = types.KeyboardButton("6 часов")
            button2 = types.KeyboardButton("10 часов")
            button3 = types.KeyboardButton("12 часов")
            markup.add(button1, button2, button3)
            time_mes = "Выбирайте удобное вам время после написания планнера."
            vars.bot.send_message(message.chat.id, time_mes, reply_markup=markup)
    except Exception as excep:
        vars.bot.send_message(message.chat.id, 'Вы не зарегистрированы')
        print(excep)


@vars.bot.message_handler(commands=['days'])
def days(message):
    if message.from_user.id in vars.all_users.keys():
        vars.all_users[message.from_user.id].days.clear()
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        button1 = types.KeyboardButton("Понедельник")
        button2 = types.KeyboardButton("Вторник")
        button3 = types.KeyboardButton("Среда")
        button4 = types.KeyboardButton("Четверг")
        button5 = types.KeyboardButton("Пятница")
        button6 = types.KeyboardButton("Суббота")
        button7 = types.KeyboardButton("Воскресенье")
        markup.add(button1, button2, button3, button4, button5, button6, button7)
        vars.bot.send_message(message.chat.id, 'Выберите удобные вам дни', reply_markup=markup)
    else:
        vars.bot.send_message(message.chat.id, 'Вы не зарегистрированы')


@vars.bot.message_handler(func=lambda message: message.reply_to_message and message.reply_to_message.message_id in vars.messages_need_to_answer)
def reply_handler(message):
    name = message.from_user.first_name + '' + message.from_user.last_name

    # This function will be called whenever a user replies to a message with an ID in message_ids
    reply_message = message.reply_to_message

    vars.gs.put_answer(name, reply_message.text, message.text)

@vars.bot.message_handler(commands=['add_gs'])
def add_gs(message):
    vars.gs.SPREADSHEET_ID = re.search(r"/d/(.*?)/edit", message.text).group(1)
    vars.bot.send_message(message.chat.id, 'Вы добавили гугл таблицу')
# send to user all commands he can use


@vars.bot.message_handler(commands=['help'])
def helper(message):
    vars.bot.send_message(message.chat.id, vars.help_message, parse_mode='html')


# adding special words to search for


@vars.bot.message_handler(commands=['keywords'])
def keyword(message):
    strnew = str(message.text).split()
    vars.keyWords.append(strnew[1])
    vars.bot.send_message(message.chat.id, f'Keyword {strnew[1]} was added', parse_mode='html')


# all cases when user sent text message


@vars.bot.message_handler(content_types=['text'])
def just_text(message):
    if message.text == 'Привет!':
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        button1 = types.KeyboardButton(f'Хелп')
        button2 = types.KeyboardButton(f'Я знаю, что делать.')
        markup.add(button1, button2)
        vars.bot.send_message(message.chat.id, f'Если не знаешь, что делать - нажми на кнопку.', reply_markup=markup)
    elif message.text == 'Хелп':
        vars.bot.send_message(message.chat.id, vars.help_message, parse_mode='html')
    elif message.text == "Я знаю, что делать.":
        vars.bot.send_message(message.chat.id, 'Принято.', parse_mode='html')
    elif message.text == "Время":
        time_mes = "По умолчанию это 8 часов после написания планнера."
        vars.bot.send_message(message.chat.id, time_mes, parse_mode='html')
        sleep(2)
        request_mes = "Вы хотите изменить время получения напоминалки?"
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        button1 = types.KeyboardButton("Да, я хочу изменить время")
        button2 = types.KeyboardButton("Нет, я не хочу изменить время")
        markup.add(button1, button2)
        vars.bot.send_message(message.chat.id, request_mes, reply_markup=markup)
    elif message.text == "Да, я хочу изменить время":
        time_editing_mes = "Кликните на команду /time"
        vars.bot.send_message(message.chat.id, time_editing_mes)
    elif message.text == "Нет, я не хочу изменить время":
        no_mes = "Хорошо. Бот будет отправлять вам напоминалки каждые 8 часов."
        vars.bot.send_message(message.chat.id, no_mes, parse_mode='html')
    elif message.text == "Дни недели":
        day_mes = "По умолчанию это каждый рабочий день"
        vars.bot.send_message(message.chat.id, day_mes, parse_mode='html')
        sleep(2)
        request_mes = "Вы хотите изменить дни недели получения напоминалок?"
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        button1 = types.KeyboardButton("Да, я хочу изменить дни.")
        button2 = types.KeyboardButton("Нет, я не хочу изменить дни.")
        markup.add(button1, button2)
        vars.bot.send_message(message.chat.id, request_mes, reply_markup=markup)
    elif message.text == "Да, я хочу изменить дни.":
        vars.bot.send_message(message.chat.id, 'Нажмите на команду /days', parse_mode='html')

    # TODO УБРАТЬ ПОЧТИ КОПИРОВАНИЕ И НАПОМНИТЬ РАССКАЗАТЬ

    elif message.text in vars.list_with_days:
        pass
        # if message.from_user.id in all_users.keys() and message.text:
        #     if message.text not in all_users[message.from_user.id].days:
        #         all_users[message.from_user.id].days.append(message.text)
        #         bot.send_message(message.chat.id, f'Вы успешно добавили {message.text}')
        #     else:
        #         bot.send_message(message.chat.id, f'У вас уже добавлен {message.text}')

    elif message.text == "Нет, я не хочу изменить дни.":
        no_mes = "Хорошо. Бот будет отправлять вам напоминалки каждый будний день."
        vars.bot.send_message(message.chat.id, no_mes, parse_mode='html')
    elif message.text == "Регистрация нового пользователя":
        instruction_mes = "Кликните на команду /register."
        vars.bot.send_message(message.chat.id, instruction_mes, parse_mode='html')

    elif message.text in vars.list_with_sked_hours.keys():
        sked_id = None
        try:
            with vars.connection.cursor() as cursor1:
                cursor1.execute(f"""SELECT mes_id FROM skeds WHERE id = {message.from_user.id}""")
                sked_id = cursor1.fetchone()[0]
        except Exception as excep:
            print("[INFO] Error while working with PostgreSQL", excep)
            hour = vars.list_with_sked_hours.get(message.text)
            vars.redis.set(sked_id, hour, hour * 3600)

    elif message.text in vars.list_with_hours.keys():
        with vars.connection.cursor() as cursor1:
            hour = vars.list_with_hours.get(message.text)
            cursor1.execute(f"""UPDATE users SET time = {hour} WHERE id = {message.from_user.id}""")
            vars.bot.send_message(message.chat.id, f'Вы изменили время получения напоминалок на {message.text}')

    # elif message.text == f'https://docs.google.com/spreadsheets/d/{re.search("/d/(.*)/", message.text).group(1)}' \
    #                      f'{re.search("/edit(.*)", message.text).group(0)}':
    #
    #     vars.bot.send_message(message.chat.id, 'Вы добавили гугл таблицу')

    else:
        for i in message.text.split():
            for j in range(len(vars.keyWords)):
                if i != vars.keyWords[j]:
                    pass
                else:
                    # json_object = json.dumps(str(message), indent = 0)
                    vars.connection.autocommit = True
                    try:
                        with vars.connection.cursor() as cursor1:
                            cursor1.execute(f"""INSERT INTO skeds (id, chat_id, mes_id) VALUES(
                            {message.from_user.id}, {message.chat.id}, {message.message_id})""")
                            name = message.from_user.first_name + '' + message.from_user.last_name
                            vars.gs.find_and_write_name("name", message.text)
                            vars.gs.put_text(name, message.text)
                        with vars.connection.cursor() as cursor2:
                            cursor2.execute(f"""SELECT time FROM users WHERE id = {message.from_user.id}""")
                            time_t = cursor2.fetchone()[0] * 1
                            print(time_t)
                            vars.redis.setex(message.message_id, time_t, message.from_user.id)
                            vars.messages_need_to_answer.append(message.message_id)
                            vars.bot.send_message(message.chat.id, "Добавлен!")
                    except Exception as excep:
                        vars.bot.send_message(message.chat.id, f'Вы не зарегистрированы {excep}')


# TODO NOT TODO BUT IT'S HERE

def answer():
    while True:
        keys = vars.redis.keys('*')
        for i in keys:
            try:
                with vars.connection.cursor() as cursor5:
                    cursor5.execute(f"""SELECT chat_id FROM skeds WHERE mes_id = {int(i)}""")
                    chat_id = cursor5.fetchone()[0]
                    if not vars.redis.exists(i):
                        print(i)
                        vars.bot.send_message(chat_id, 'blablalba', reply_to_message_id=int(i))
                        with vars.connection.cursor() as cursor6:
                            cursor6.execute(f"""DELETE FROM skeds where mes_id = {int(i)}""")
            except Exception as excep:
                print(f'Вы не зарегистрированы {excep}')


thread_for_answering = threading.Thread(target=answer, args=(), daemon=True)
thread_for_answering.start()

vars.bot.polling(none_stop=True)
