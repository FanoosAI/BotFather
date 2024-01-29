host = "https://parsi.ai"


def set_host(host_server: str):
    global host
    host = host_server


# should be used as decorator on other functions
def with_auth(path, authentication: str):
    return f"{path}?access_token={authentication}"


def get_room_members(room_id: str, authentication: str):
    return 'GET', with_auth(f"{host}/_matrix/client/v3/rooms/{room_id}/joined_members", authentication)


def get_joined_rooms(authentication: str):
    return 'GET', with_auth(f"{host}/_matrix/client/v3/joined_rooms", authentication)


def leave_room(room_id: str, authentication: str):
    return 'POST', with_auth(f"{host}/_matrix/client/r0/rooms/{room_id}/leave", authentication)


def get_user_info(user_id: str):
    return 'GET', f'{host}/_matrix/client/v3/profile/{user_id}'


def get_registered_bots():
    return 'GET', f'{host}/marketplace/public-bots'


def register_bot():
    return 'POST', f'{host}/marketplace/register'
