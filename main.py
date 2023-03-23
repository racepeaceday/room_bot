import telebot
from telebot import types
from telebot.types import ReplyKeyboardRemove

import room_data
import user_data
from room import Room
from configparser import ConfigParser

from user import User

config = ConfigParser()
config.read('config.ini')

token = config.get('bot', 'token')
admin_id = config.get('bot', 'admin_id')

bot = telebot.TeleBot(token)

rooms = []
requests = []

room_data.load_rooms()
user_data.load_users()


@bot.message_handler(commands=['start', 'help'])
def handler(message):
    if not user_data.user_exists_with_id(message.from_user.id):
        load = User(user_id=message.from_user.id)
        user_data.users.append(load)
        user_data.user_db.insert_one(
            {
                'id': message.from_user.id,
                'room': 'None'
            }
        )
    user = user_data.get_user_with_id(message.from_user.id)
    if user.room:
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        markup.add(types.KeyboardButton('Выйти из комнаты'))
        bot.send_message(message.chat.id, text=f'Вы находитесь в комнате {user.room.name}', reply_markup=markup)
    else:
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        buttons = [
            types.KeyboardButton("Войти в комнату"),
            types.KeyboardButton("Создать комнату"),
            types.KeyboardButton("Удалить комнату"),
            types.KeyboardButton("Добавить гаранта")
        ]
        markup.add(buttons[0])
        if user.garant or str(message.from_user.id) == str(admin_id):
            markup.add(buttons[1])
            markup.add(buttons[2])
            markup.add(buttons[3])
        bot.send_message(
            message.chat.id,
            'Добро пожаловать в комнаты! Воспользуйтесь следующими функциями:',
            reply_markup=markup
        )


@bot.message_handler(func=lambda message: True)
def handler(message):
    user = user_data.get_user_with_id(message.from_user.id)
    if user:
        if message.text == "Добавить гаранта":
            markup = types.InlineKeyboardMarkup()
            for user in user_data.users:
                markup.add(types.InlineKeyboardButton(user.user_id, callback_data='ADD_GARANT_' + str(user.user_id)))
            bot.send_message(message.chat.id, 'Выберите ID пользователя:',
                             reply_markup=markup)
            return
        if message.text == "Удалить комнату":
            markup = types.InlineKeyboardMarkup()
            for room in room_data.rooms:
                markup.add(types.InlineKeyboardButton(room.name, callback_data='DELETE_' + room.name))
            bot.send_message(message.chat.id, 'Выберите комнату, которую хотите удалить из списка:',
                             reply_markup=markup)
            return
        if message.text == "Выйти из комнаты":
            markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
            buttons = [
                types.KeyboardButton("Войти в комнату"),
                types.KeyboardButton("Создать комнату"),
                types.KeyboardButton("Удалить комнату"),
                types.KeyboardButton("Добавить гаранта")
            ]
            markup.add(buttons[0])
            if user.garant or str(message.from_user.id) == str(admin_id):
                markup.add(buttons[1])
                markup.add(buttons[2])
                markup.add(buttons[3])
            bot.send_message(message.chat.id, 'Вы вышли из комнаты', reply_markup=markup)
            user.room.users.remove(user.user_id)
            user.room = None
            return

        if message.text == "Создать комнату":
            bot.send_message(
                message.chat.id,
                'Введите название комнаты (до 16 символов):'
            )
            bot.register_next_step_handler(message, set_name)
            return

        if message.text == "Войти в комнату":
            markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
            buttons = []
            for room in room_data.get_all():
                if len(room.users) < room.limit:
                    buttons.append(types.KeyboardButton(room.name))
            for button in buttons:
                markup.add(button)
            bot.send_message(message.chat.id, 'Выберите комнату:', reply_markup=markup)
            return

        if message.text in room_data.get_room_name_list():
            bot.send_message(message.chat.id, 'Введите пароль комнаты:', reply_markup=ReplyKeyboardRemove())
            bot.register_next_step_handler(message, login, room_data.get_room_with_name(message.text))
            return

        if message.text == 'Позвать гаранта':
            i = 1
            markup = types.InlineKeyboardMarkup()
            for garant in user_data.users:
                if garant.garant and not garant.room:
                    markup.add(types.InlineKeyboardButton(f'Гарант №{i}', callback_data=garant.user_id))
                    i += 1
            bot.send_message(message.chat.id, 'Выберите одного из свободных гарантов:', reply_markup=markup)
            return

        if message.text == 'Принять':
            for request in requests:
                if message.from_user.id == request[1]:
                    user_data.get_user_with_id(request[0]).room.users.append(user.user_id)
                    user.room = user_data.get_user_with_id(request[0]).room
                    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
                    markup.add(types.KeyboardButton('Позвать гаранта'))
                    markup.add(types.KeyboardButton('Выйти из комнаты'))
                    bot.send_message(message.chat.id, f'Вы вошли в комнату '
                                                      f'{user_data.get_user_with_id(request[0]).room.name}',
                                     reply_markup=markup)
            return

        if user.room:
            for user_in_room in user.room.users:
                if user_in_room != user.user_id:
                    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
                    if not user_in_room.garant:
                        markup.add(types.KeyboardButton('Позвать гаранта'))
                    markup.add(types.KeyboardButton('Выйти из комнаты'))
                    if not user.garant:
                        bot.send_message(user_in_room, message.text, reply_markup=markup)
                    else:
                        bot.send_message(user_in_room, text='Гарант: ' + message.text, reply_markup=markup)


def login(message, room):
    pswd = message.text
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(types.KeyboardButton('Позвать гаранта'))
    markup.add(types.KeyboardButton('Выйти из комнаты'))
    if room.password == pswd:
        bot.send_message(message.chat.id, f'Вы вошли в комнату {room.name}', reply_markup=markup)
        room.users.append(message.from_user.id)
        user_data.get_user_with_id(message.chat.id).room = room
    else:
        bot.send_message(message.chat.id, 'Неверный пароль')


def set_name(message):
    global name
    name = message.text
    if len(message.text) < 16:
        bot.register_next_step_handler(message, set_password)
        bot.send_message(
            message.chat.id,
            'Придумайте пароль для входа:'
        )
    else:
        bot.register_next_step_handler(message, set_name)


def set_password(message):
    global password
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    buttons = [
        types.KeyboardButton("Войти в комнату"),
        types.KeyboardButton("Создать комнату")
    ]
    markup.add(buttons[0])
    markup.add(buttons[1])
    password = message.text
    room = Room(room_id=len(room_data.get_all()), name=name, password=password, owner=message.from_user.id)
    room_data.get_all().append(room)
    room_data.rooms_db.insert_one(
        {
            'id': room.room_id,
            'owner': message.from_user.id,
            'name': room.name,
            'password': room.password,
            'users': room.users,
            'messages': room.messages
        }
    )
    bot.send_message(
        message.chat.id,
        'Комната создана!',
        reply_markup=markup
    )


@bot.callback_query_handler(func=lambda call: True)
def handler(call):
    if 'DELETE_' in call.data:
        room = room_data.get_room_with_name(call.data.split('_')[1])
        room_data.delete_room(room)
        bot.send_message(call.from_user.id, 'Комната удалена')
    if 'ADD_GARANT_' in call.data:
        new_garant = user_data.get_user_with_id(int(call.data.split('_')[2]))
        new_garant.garant = True
        bot.send_message(call.from_user.id, f'Пользователь с id {new_garant.user_id} назначен гарантом')
        bot.send_message(new_garant.user_id, 'Вы были назначены гарантом')
    for g in user_data.users:
        if call.data == str(g.user_id):
            markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
            buttons = [
                types.KeyboardButton("Принять"),
                types.KeyboardButton("Отклонить")
            ]
            markup.add(buttons[0])
            markup.add(buttons[1])
            requests.append([call.from_user.id, g.user_id])
            bot.send_message(g.user_id, 'Вы были приглашены в беседу в качестве гаранта.', reply_markup=markup)


bot.infinity_polling()
room_data.save_rooms()
user_data.save_users()
