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


@bot.message_handler(commands=['ban'])
def handler(message):
    if message.from_user.id == int(admin_id):
        bot.send_message(message.chat.id, 'Введите ID пользователя:')
        bot.register_next_step_handler(message, ban)


def ban(message):
    banned_id = int(message.text)
    user = user_data.get_user_with_id(banned_id)
    user.ban = True
    bot.send_message(banned_id, 'Вы были заблокированы за нарушение правил.')
    bot.send_message(message.from_user.id, 'Пользователь заблокирован.')
    if user.room:
        user.room.users.remove(user)
        user.room = None


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
    if user.ban:
        bot.send_message(message.chat.id, 'Вы были заблокированы за нарушение правил.\nДоступ к боту ограничен.')
        return
    if user.room:
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        markup.add(types.KeyboardButton('🚪Выйти из комнаты'))
        bot.send_message(message.chat.id, text=f'Вы находитесь в комнате {user.room.name}', reply_markup=markup)
    else:
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        buttons = [
            types.KeyboardButton("📝Создать комнату"),
            types.KeyboardButton("🔑Войти в комнату"),
            types.KeyboardButton("🚪Мои комнаты"),
            types.KeyboardButton("📈Место  для рекламы"),
            types.KeyboardButton("🏦Наши проекты"),
            types.KeyboardButton("🧾Правила"),
            types.KeyboardButton("⚙️Комнаты")
        ]
        markup.add(buttons[0], buttons[1], buttons[2])
        markup.add(buttons[3], buttons[4], buttons[5])
        if user.user_id == int(admin_id):
            markup.add(buttons[6])
        bot.send_message(
            message.chat.id,
            f'JUMBAS TEAM 🌐 рады приветствовать вас в боте "JUMBAS ROOMS"🚪\n\n'
            f'Данный бот создан для проведения анонимных сделок между юзерами. 🤫'
            f'Хотите остаться посредником в сделке, но хотите оптимизировать передачу информации?📑'
            f'Этот бот для вас.🤖',
            reply_markup=markup
        )


@bot.message_handler(func=lambda message: True)
def handler(message):
    user = user_data.get_user_with_id(message.from_user.id)
    if user.ban:
        bot.send_message(message.chat.id, 'Вы были заблокированы за нарушение правил.\nДоступ к боту ограничен.')
        return
    if user:
        if message.text == "⚙️Комнаты":
            markup = types.InlineKeyboardMarkup()
            buttons = []
            for room in room_data.rooms:
                buttons.append(types.InlineKeyboardButton(room.name, callback_data="ADMIN_" + room.name))
            for button in buttons:
                markup.add(button)
            if len(buttons) == 0:
                bot.send_message(message.chat.id, "Комнат еще нет")
            else:
                bot.send_message(message.chat.id, f'Комнаты бота:', reply_markup=markup)
            return
        if message.text == "В меню":
            markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
            buttons = [
                types.KeyboardButton("📝Создать комнату"),
                types.KeyboardButton("🔑Войти в комнату"),
                types.KeyboardButton("🚪Мои комнаты"),
                types.KeyboardButton("📈Место  для рекламы"),
                types.KeyboardButton("🏦Наши проекты"),
                types.KeyboardButton("⚙️Комнаты")
            ]
            markup.add(buttons[0], buttons[1], buttons[2])
            markup.add(buttons[3], buttons[4], buttons[5])
            if user.user_id == int(admin_id):
                markup.add(buttons[6])
            bot.send_message(
                message.chat.id,
                f'JUMBAS TEAM 🌐 рады приветствовать вас в боте "JUMBAS ROOMS"🚪\n\n'
                f'Данный бот создан для проведения анонимных сделок между юзерами. 🤫'
                f'Хотите остаться посредником в сделке, но хотите оптимизировать передачу информации?📑'
                f'Этот бот для вас.🤖',
                reply_markup=markup
            )
            return
        if message.text == "🛑Аларм":
            if user.room is not None:
                markup = types.InlineKeyboardMarkup()
                markup.add(types.InlineKeyboardButton('✅Подтвердить', callback_data='ALARM_' + user.room.name),
                           types.InlineKeyboardButton('🔙Отмена', callback_data='CANCEL'))
                bot.send_message(message.chat.id, f'Данная кнопка создана для сообщении о нарушений правил. 🧾\n'
                                                  f'После ее нажатия добавится администратор в комнату для проверки '
                                                  f'соблюдения правил.\n '
                                                  f'При ложном вызове администратор может также выдать бан.📵\n\n'
                                                  f'Подтверждаешь нарушение правил и добавление администратора?',
                                 reply_markup=markup)
            return
        if message.text == "🚪Мои комнаты":
            markup = types.InlineKeyboardMarkup()
            buttons = []
            for room in room_data.rooms:
                if room.owner == message.from_user.id:
                    buttons.append(types.InlineKeyboardButton(room.name, callback_data="MY_" + room.name))
            for button in buttons:
                markup.add(button)
            if len(buttons) == 0:
                bot.send_message(message.chat.id, "У вас еще нет ни одной комнаты")
            else:
                bot.send_message(message.chat.id, f'Ваши комнаты:', reply_markup=markup)
            return
        if message.text == "🧾Правила":
            bot.send_message(
                message.chat.id,
                f'Данный бот служит исключительно для обмена информацией по заказу🤝\n\n'
                f'1️⃣Запрещено обмениваться личной информацией, с помощью которой можно связаться вне бота.\n'
                f'2️⃣Запрещено выдавать свои собственные реквизиты для оплаты.\n'
                f'3️⃣Запрещена агрессия и оскорбления.\n\n'
                f'За несоблюдение правил будет выдаваться бан во всех проектах JUMBAS TEAM📵'
            )
            return
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
        if message.text == "🚪Выйти из комнаты":
            markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
            buttons = [
                types.KeyboardButton("📝Создать комнату"),
                types.KeyboardButton("🔑Войти в комнату"),
                types.KeyboardButton("🚪Мои комнаты"),
                types.KeyboardButton("📈Место  для рекламы"),
                types.KeyboardButton("🏦Наши проекты"),
                types.KeyboardButton("🧾Правила"),
            ]
            markup.add(buttons[0], buttons[1], buttons[2])
            markup.add(buttons[3], buttons[4], buttons[5])
            if user.room is None:
                bot.send_message(message.chat.id, 'Вы не состоите в комнате', reply_markup=markup)
                return
            bot.send_message(message.chat.id, 'Вы вышли из комнаты', reply_markup=markup)
            user.room.users.remove(user.user_id)
            user.room = None
            return
        if message.text == "🏦Наши проекты":
            bot.send_message(
                message.chat.id,
                'Здесь собраны все проекты от JUMBAS TEAM 👉 @racepeaceday (coder)'
            )
        if message.text == "📈Место  для рекламы":
            bot.send_message(message.chat.id,
                             f'Хотите разместить рекламу своего проекта в данном боте?\n'
                             f'📜 Пишите 📲  @racepeaceday (coder)')
        if message.text == "📝Создать комнату":
            bot.send_message(
                message.chat.id,
                'Введите название комнаты (до 16 символов):'
            )
            bot.register_next_step_handler(message, set_name)
            return

        if message.text == "🔑Войти в комнату":
            markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
            buttons = []
            for room in room_data.get_all():
                if len(room.users) < room.limit:
                    buttons.append(types.KeyboardButton(room.name))
            for button in buttons:
                markup.add(button)
            markup.add(types.KeyboardButton("В меню"))
            bot.send_message(message.chat.id, 'Выберите комнату:', reply_markup=markup)
            return

        if message.text in room_data.get_room_name_list():
            bot.send_message(message.chat.id, 'Введите пароль комнаты:', reply_markup=ReplyKeyboardRemove())
            bot.register_next_step_handler(message, login, room_data.get_room_with_name(message.text))
            return

        if message.text == '➕Позвать гаранта':
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
                    for member in user.room.users:
                        if member != message.from_user.id:
                            bot.send_message(member,
                                             f'Приветствую 👋🏻 Я @{message.from_user.username} 🌐 буду проводить вам '
                                             f'сделку!\n'
                                             f'\nОтзывы - (ссылка)💯\n\n'
                                             f'Услуги гаранта👇🏻\n'
                                             f'До 100💲 - комиссия 7%\n'
                                             f'От 100$-1000💲 - комиссия 5%\n'
                                             f'От 1000💲 - комиссия 3%\n'
                                             f'От 1000💲 - комиссия 3%\n'
                                             f'+2💲 на комиссию сети\n\n'
                                             f'Транзакции лучше всего  производить в USDT. '
                                             f'После окончания сделки и согласия 2х сторон, произведется выплата или '
                                             f'выдача данных.')
                    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
                    markup.add(types.KeyboardButton('🚪Выйти из комнаты'))
                    bot.send_message(message.chat.id, f'Вы вошли в комнату '
                                                      f'{user_data.get_user_with_id(request[0]).room.name}',
                                     reply_markup=markup)
            return

        if user.room:
            user.room.messages.append(
                {
                    'user': user.user_id,
                    'message': message.text
                }
            )
            for user_in_room in user.room.users:
                if user.user_id != user_in_room:
                    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
                    markup.add(types.KeyboardButton('➕Позвать гаранта'))
                    markup.add(types.KeyboardButton('🛑Аларм'))
                    markup.add(types.KeyboardButton('🚪Выйти из комнаты'))
                    if user.user_id == int(admin_id):
                        bot.send_message(user_in_room, '[Админ]: ' + message.text, reply_markup=markup)
                        return
                    if user.garant:
                        bot.send_message(user_in_room, '[Гарант]: ' + message.text, reply_markup=markup)
                        return
                    else:
                        bot.send_message(user_in_room, f'[{user.user_id}]: ' + message.text, reply_markup=markup)
                        return


def login(message, room):
    pswd = message.text
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(types.KeyboardButton('➕Позвать гаранта'))
    markup.add(types.KeyboardButton('🛑Аларм'))
    markup.add(types.KeyboardButton('🚪Выйти из комнаты'))
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
        types.KeyboardButton("📝Создать комнату"),
        types.KeyboardButton("🔑Войти в комнату"),
        types.KeyboardButton("🚪Мои комнаты"),
        types.KeyboardButton("📈Место  для рекламы"),
        types.KeyboardButton("🏦Наши проекты"),
        types.KeyboardButton("🧾Правила"),
    ]
    markup.add(buttons[0], buttons[1], buttons[2])
    markup.add(buttons[3], buttons[4], buttons[5])
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
        f'Комната {room.name} создана!',
        reply_markup=markup
    )


@bot.callback_query_handler(func=lambda call: True)
def handler(call):
    if 'BACK_' in call.data:
        bot.delete_message(call.from_user.id, call.message.id)
        room = room_data.get_room_with_name(call.data.split('_')[1])
        markup = types.InlineKeyboardMarkup()
        if room.limit > 2:
            markup.add(types.InlineKeyboardButton('Убрать слот (-1)', callback_data='REMOVE_SLOT_' + room.name))
        markup.add(types.InlineKeyboardButton('Добавить слот (+1)', callback_data='ADD_SLOT_' + room.name))
        markup.add(types.InlineKeyboardButton('Удалить комнату', callback_data='DELETE_' + room.name))
        markup.add(types.InlineKeyboardButton('История сообщений', callback_data='HISTORY_' + room.name))
        markup.add(types.InlineKeyboardButton('Назад', callback_data='ADMINROOMS'))
        bot.send_message(call.from_user.id, f'🚪 Комната {room.name}'
                                            f'\n'
                                            f'\n🔎 Создатель: {room.owner}'
                                            f'\n👥 Количество участников: {len(room.users)}/{room.limit}'
                                            f'\n🔑 Пароль: {room.password}'
                                            f'\n'
                                            f'\n⚙️ Действия с комнатой:', reply_markup=markup)
    if 'HISTORY_' in call.data:
        room = room_data.get_room_with_name(call.data.split('_')[1])
        text = 'История сообщений:\n'
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton('Назад', callback_data='BACK_' + room.name))
        for message in room.messages:
            text += f'\n[{message["user"]}]: {message["message"]}\n'
        bot.send_message(admin_id, f'{text}', reply_markup=markup)
        bot.delete_message(call.from_user.id, call.message.id)
    if 'ADMIN_' in call.data:
        room = room_data.get_room_with_name(call.data.split('_')[1])
        markup = types.InlineKeyboardMarkup()
        if room.limit > 2:
            markup.add(types.InlineKeyboardButton('Убрать слот (-1)', callback_data='REMOVE_SLOT_' + room.name))
        markup.add(types.InlineKeyboardButton('Добавить слот (+1)', callback_data='ADD_SLOT_' + room.name))
        markup.add(types.InlineKeyboardButton('Удалить комнату', callback_data='DELETE_' + room.name))
        markup.add(types.InlineKeyboardButton('История сообщений', callback_data='HISTORY_' + room.name))
        markup.add(types.InlineKeyboardButton('Назад', callback_data='ADMINROOMS'))
        bot.delete_message(call.from_user.id, call.message.id)
        bot.send_message(call.from_user.id, f'🚪 Комната {room.name}'
                                            f'\n'
                                            f'\n🔎 Создатель: {room.owner}'
                                            f'\n👥 Количество участников: {len(room.users)}/{room.limit}'
                                            f'\n🔑 Пароль: {room.password}'
                                            f'\n'
                                            f'\n⚙️ Действия с комнатой:', reply_markup=markup)
    if call.data == 'CANCEL':
        bot.delete_message(call.from_user.id, call.message.id)
    if 'ALARM_' in call.data:
        bot.delete_message(call.from_user.id, call.message.id)
        bot.send_message(call.from_user.id, 'Админ добавлен.')
        room = room_data.get_room_with_name(call.data.split('_')[1])
        admin = user_data.get_user_with_id(int(admin_id))
        text = 'История сообщений:\n'
        for message in room.messages:
            text += f'\n[{message["user"]}]: {message["message"]}\n'
        bot.send_message(admin_id, f'В комнате {room.name} были замечены нарушения.\nВы были автоматически '
                                   f'добавлены.\n\n'
                                   f'{text}')
        admin.room = room
        room.users.append(admin.user_id)
    if call.data == 'ADMINROOMS':
        bot.delete_message(call.from_user.id, call.message.id)
        markup = types.InlineKeyboardMarkup()
        buttons = []
        for room in room_data.rooms:
            buttons.append(types.InlineKeyboardButton(room.name, callback_data="ADMIN_" + room.name))
        for button in buttons:
            markup.add(button)
        if len(buttons) == 0:
            bot.send_message(call.from_user.id, "Комнат еще нет")
        else:
            bot.send_message(call.from_user.id, f'Комнаты бота:', reply_markup=markup)
    if call.data == 'ROOMS':
        bot.delete_message(call.from_user.id, call.message.id)
        markup = types.InlineKeyboardMarkup()
        buttons = []
        for room in room_data.rooms:
            if room.owner == call.from_user.id:
                buttons.append(types.InlineKeyboardButton(room.name, callback_data="MY_" + room.name))
        for button in buttons:
            markup.add(button)
        if len(buttons) == 0:
            bot.send_message(call.from_user.id, "У вас еще нет ни одной комнаты")
        else:
            bot.send_message(call.from_user.id, f'Ваши комнаты:', reply_markup=markup)
    if 'MY_' in call.data:
        room = room_data.get_room_with_name(call.data.split('_')[1])
        markup = types.InlineKeyboardMarkup()
        if room.limit > 2:
            markup.add(types.InlineKeyboardButton('Убрать слот (-1)', callback_data='REMOVE_SLOT_' + room.name))
        markup.add(types.InlineKeyboardButton('Добавить слот (+1)', callback_data='ADD_SLOT_' + room.name))
        markup.add(types.InlineKeyboardButton('Удалить комнату', callback_data='DELETE_' + room.name))
        markup.add(types.InlineKeyboardButton('Назад', callback_data='ROOMS'))
        bot.delete_message(call.from_user.id, call.message.id)
        bot.send_message(call.from_user.id, f'🚪 Комната {room.name}'
                                            f'\n'
                                            f'\n👥 Количество участников: {len(room.users)}/{room.limit}'
                                            f'\n🔑 Пароль: {room.password}'
                                            f'\n'
                                            f'\n⚙️ Действия с комнатой:', reply_markup=markup)
    if 'ADD_SLOT_' in call.data:
        room = room_data.get_room_with_name(call.data.split('_')[2])
        room.limit += 1
        markup = types.InlineKeyboardMarkup()
        if room.limit > 2:
            markup.add(types.InlineKeyboardButton('Убрать слот (-1)', callback_data='REMOVE_SLOT_' + room.name))
        markup.add(types.InlineKeyboardButton('Добавить слот (+1)', callback_data='ADD_SLOT_' + room.name))
        markup.add(types.InlineKeyboardButton('Удалить комнату', callback_data='DELETE_' + room.name))
        markup.add(types.InlineKeyboardButton('Назад', callback_data='ROOMS'))
        bot.delete_message(call.from_user.id, call.message.id)
        bot.send_message(call.from_user.id, f'🚪 Комната {room.name}'
                                            f'\n'
                                            f'\n👥 Количество участников: {len(room.users)}/{room.limit}'
                                            f'\n🔑 Пароль: {room.password}'
                                            f'\n'
                                            f'\n⚙️ Действия с комнатой:', reply_markup=markup)
    if 'REMOVE_SLOT_' in call.data:
        room = room_data.get_room_with_name(call.data.split('_')[2])
        room.limit -= 1
        markup = types.InlineKeyboardMarkup()
        if room.limit > 2:
            markup.add(types.InlineKeyboardButton('Убрать слот (-1)', callback_data='REMOVE_SLOT_' + room.name))
        markup.add(types.InlineKeyboardButton('Добавить слот (+1)', callback_data='ADD_SLOT_' + room.name))
        markup.add(types.InlineKeyboardButton('Удалить комнату', callback_data='DELETE_' + room.name))
        markup.add(types.InlineKeyboardButton('Назад', callback_data='ROOMS'))
        bot.delete_message(call.from_user.id, call.message.id)
        bot.send_message(call.from_user.id, f'🚪 Комната {room.name}'
                                            f'\n'
                                            f'\n👥 Количество участников: {len(room.users)}/{room.limit}'
                                            f'\n🔑 Пароль: {room.password}'
                                            f'\n'
                                            f'\n⚙️ Действия с комнатой:', reply_markup=markup)
    if 'DELETE_' in call.data:
        room = room_data.get_room_with_name(call.data.split('_')[1])
        room_data.delete_room(room)
        bot.delete_message(call.from_user.id, call.message.id)
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
