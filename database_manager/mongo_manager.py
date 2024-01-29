import datetime

import pymongo
import yaml

from database_manager import exceptions

with open('configuration.yaml') as conf_file:
    conf = yaml.safe_load(conf_file)["databases"]["mongo"]

# setup mongo connection
client = pymongo.MongoClient(
    f"mongodb://{conf['host']}:{conf['port']}",
    username=conf['user'],
    password=conf['password'],
    authSource=conf['database'],
)
db = client[conf['database']]
collection = db[conf['collection']]
admin_collection = db[conf['admin_collection']]


def register_entry(data: dict):
    collection.insert_one(data)


def register_request(bot_username: str, registrar: str, name: str, room: str, time: datetime.datetime = datetime.datetime.now()):
    if get_request_by_username(bot_username):
        raise exceptions.RepeatedEntryException()

    register_entry({
        'bot_username': bot_username,
        'registrar': registrar,
        'request_room': room,
        'name': name,
        'time': time,
        'status': '?'
    })


def update_request_status(bot_username: str, status: str):
    collection.update_one({'bot_username': bot_username}, {'$set': {'status': status}})


def get_request_by_username(bot_username: str):
    return collection.find_one({'bot_username': bot_username}, {'_id': 0})


def register_admin_room(room_id: str):
    admin_collection.delete_many({})
    admin_collection.insert_one({'room': room_id})


def get_admin_room():
    return admin_collection.find_one({}).get('room')
