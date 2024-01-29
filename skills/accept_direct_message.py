# bot will accept all invitations to all rooms as long as they are a direct messages

import logging
import asyncio

from opsdroid.matchers import match_event, match_crontab, match_parse
from opsdroid.events import Message, JoinRoom, UserInvite, LeaveRoom
from opsdroid.skill import Skill

import api_caller
from api_caller import api_maker
from database_manager import mongo_manager


class AcceptDirectMessageSkill(Skill):

    def __init__(self, opsdroid, config):
        super(AcceptDirectMessageSkill, self).__init__(opsdroid, config)
        api_maker.set_host(self.opsdroid.config['connectors']['matrix']['homeserver'])

    @match_event(UserInvite)
    async def accept_direct_message(self, event):
        logging.info(f"accept_direct_message -> {event}")
        response = JoinRoom()
        logging.info(f"response: {response}")

        # admin_username = self.config.get('admin_username')
        # if event.user_id == admin_username:
        #     room_id = event.target
        #     logging.info(f'New chat with the admin has been recognized -> %s', room_id)
        #     mongo_manager.register_admin_room(room_id)
        await event.respond(response)

    @match_crontab('0 * * * *')
    async def leave_empty_room(self, event):

        access_token = self.opsdroid.connectors[0].access_token
        method, rooms_api = api_maker.get_joined_rooms(access_token)
        rooms = await api_caller.call_api(method, rooms_api, None)
        tasks = [
            asyncio.ensure_future(AcceptDirectMessageSkill.get_room_members(room, access_token))
            for room in rooms.get('joined_rooms')
        ]
        results = await asyncio.gather(*tasks)
        for room, result in results:
            if not result.get('joined') or len(result.get('joined')) == 1:
                logging.info(f"Leaving room {room} because it was empty!")
                await api_caller.call_api(*api_maker.leave_room(room, access_token), None)

        return

    @match_parse('leave empty rooms')
    async def leave_empty_rooms_by_command(self, event):
        await self.leave_empty_room(event)

    @staticmethod
    async def get_room_members(room, authentication):
        return room, await api_caller.call_api(*api_maker.get_room_members(room, authentication), None)
