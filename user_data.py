from pymongo import MongoClient

import room_data
from user import User

database_client = MongoClient("mongodb://localhost:27017")
database = database_client['users']

user_db = database['users']
users = []


def load_users():
    for res in user_db.find():
        user = User(res['id'])
        user.garant = res['garant']
        if res['room'] != 'None':
            user.room = room_data.get_room_with_name(res['room'])
        users.append(user)
    print('Пользователи загружены')


def save_users():
    for user in users:
        user_db.update_one(
            {
                'id': user.user_id
            },
            {
                '$set':
                    {
                        'id': user.user_id,
                        'room': user.room.name if user.room else 'None',
                        'garant': user.garant
                    }
            }
        )
    print('Пользователи сохранены')


def get_user_with_id(user_id):
    u = None
    for user in users:
        if user_id == user.user_id:
            u = user
    return u


def user_exists_with_id(user_id):
    for user in users:
        if user.user_id == user_id:
            return True
    return False


def get_all():
    return users
