from pymongo import MongoClient

from room import Room

database_client = MongoClient("mongodb://localhost:27017")
database = database_client['rooms']

rooms_db = database['rooms']
rooms = []


def load_rooms():
    for res in rooms_db.find():
        room = Room(room_id=res['id'], password=res['password'], name=res['name'], owner=res['owner'])
        room.users = res['users']
        room.messages = res['messages']
        rooms.append(room)
    print('Комнаты загружены')


def delete_room(room):
    rooms_db.delete_one(
        {
            'id': room.room_id
        }
    )
    rooms.remove(room)


def save_rooms():
    for room in rooms:
        rooms_db.update_one(
            {
              'id': room.room_id
            },
            {
                "$set":
                    {
                        'id': room.room_id,
                        'owner': room.owner,
                        'name': room.name,
                        'password': room.password,
                        'users': room.users,
                        'messages': room.messages
                    }
            }

        )
    print('Комнаты сохранены')


def get_room_name_list():
    name_list = []
    for room in rooms:
        name_list.append(room.name)
    return name_list


def get_room_with_name(name):
    r = None
    for room in rooms:
        if room.name == name:
            r = room
    return r


def get_all():
    return rooms
