class Room:

    def __init__(self, room_id, password, name, owner):
        self.room_id = room_id
        self.password = password
        self.name = name
        self.limit = 2
        self.owner = owner
        self.users = []
        self.messages = []
