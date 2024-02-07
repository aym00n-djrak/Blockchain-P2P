class ConnectedUsers :
    users = []

    @staticmethod
    def add_user(username):
        ConnectedUsers.users.append(username)

    @staticmethod
    def remove_user(username):
        ConnectedUsers.users.remove(username)

    @staticmethod
    def is_user_active(username):
        if username in ConnectedUsers.users:
            return True
        else:
            return False

    @staticmethod
    def get_connected_users():
        return ConnectedUsers.users



