import logging
import re
from typing import Optional

from opsdroid.skill import Skill
from opsdroid.matchers import match_parse
from opsdroid.events import Message
from yaml import safe_load

import api_caller
from api_caller import api_maker, call_api
from database_manager import mongo_manager, exceptions as database_exceptions

"""
Any user can ask for a bot to be registered this way.
But the request has to approved by the admin.
When a request has been submitted through a direct message to bot father, the request will be sent to admin
admin can respond with "accept", "reject" or "ban".
if a bot is banned, requests for that bot_username will automatically be rejected without being sent to admin.
"""


class RegisterBotSkill(Skill):

    def __init__(self, opsdroid, config):
        super(RegisterBotSkill, self).__init__(opsdroid, config)
        with open('api_key.yaml', 'r') as api_key_file:
            self.marketplace_api_key = safe_load(api_key_file)['api_key']

    @match_parse('register {bot_username} as {gholam}')
    async def register_bot_with_name(self, event):
        logging.info(f"Register bot skill -> {event}")
        registrar = event.user_id
        request_room = event.target
        bot_username = event.entities['bot_username']['value']
        bot_username = bot_username.split('as')[0].strip()
        bot_name = event.entities['gholam']['value']
        await self.register(event, bot_username, registrar, bot_name, request_room)

    @match_parse('register {bot_username}')
    async def register_bot_with_username(self, event):
        logging.info(f"Register bot skill -> {event}")
        registrar = event.user_id
        request_room = event.target
        bot_username = event.entities['bot_username']['value']
        await self.register(event, bot_username, registrar, None, request_room)

    async def register(self, event, bot_username: str, registrar: str, bot_name: Optional[str], room: str):
        # check if username is valid!
        if not RegisterBotSkill.is_username_valid(bot_username):
            await event.respond("Please send the username in the correct format: @bot_name:server.domain"
                                "\n Keep in mind that bot names should start with bot_"
                                "\n for example: @bot_father:parsi.ai")
            return

        # call synapse api to see if username exists
        bot_info = await api_caller.call_api(*api_maker.get_user_info(bot_username))
        if bot_info.get('errcode') == 'M_NOT_FOUND':
            await event.respond('Username not found! You must first create the account, then register it here!')
            return
        elif bot_name is None:
            bot_name = bot_info.get('displayname')

        # check marketplace
        registered_bots = await call_api(*api_maker.get_registered_bots())
        if registered_bots and bot_username in {i['username'] for i in registered_bots}:
            await event.respond('This bot has already been registered!')
            return

        # register request in database
        try:
            mongo_manager.register_request(bot_username, registrar, bot_name, room)
        except database_exceptions.RepeatedEntryException:
            req_info = mongo_manager.get_request_by_username(bot_username)
            if req_info['status'] == '?':
                await event.respond('This bot has already been requested!')
            elif req_info['status'] == 'BANNED':
                await event.respond('Unfortunately this bot has been banned by the admin!')
            # If it's rejected, we'll let them ask again!
            return

        # send request to admin
        admin_room = mongo_manager.get_admin_room()
        if not admin_room:
            await event.respond('Sorry! This feature has not yet been activated by the admin!')
            return

        try:
            message = Message(
                text=f"New registry request.\nBot: {bot_username}\nRegistrar: {registrar}\nName: {bot_name}",
                target=admin_room
            )
            await self.opsdroid.send(message)
        except Exception:
            # the last room registered by admin is deactivated and admin hasn't started a new chat yet!
            await event.respond('Sorry! This feature has not yet been activated by the admin!')
            return

        await event.respond('request has been sent to admin for approval')

    @match_parse('accept {bot_username}')
    async def accept_bot(self, event):
        bot_username = event.entities['bot_username']['value']
        logging.info(f"Bot {bot_username} has been approved by admin")
        request_info = mongo_manager.get_request_by_username(bot_username)
        if not request_info:
            await event.respond(f'No requests found for {bot_username}')
            return
        # call marketplace api to register the bot
        request_body = {
            'username': request_info['bot_username'],
            'name': request_info['name'],
            'description': 'Submitted by BotFather',  # maybe TO-DO: Add description feature
            'registered_by': '@bot_father:parsi.ai',
            'registered_at': request_info['time'].isoformat()
        }
        request_headers = {'Authorization': self.marketplace_api_key}
        status, response = await \
            api_caller.call_api_with_status(*api_maker.register_bot(), request_body, request_headers)
        if status != 200:
            logging.error('REGISTERING @ MARKETPLACE FAILED!!!')
            logging.error(response)

        # register result in database
        mongo_manager.update_request_status(bot_username, 'APPROVED')

        # send message to request submitter to inform them that the request has been approved
        target = request_info['request_room']
        registrar = request_info['registrar']
        await self.opsdroid.send(
            Message(
                text=f'Congratulations {registrar}! your bot - '
                     f'{bot_username} - has just been approved on the marketplace!',
                target=target
            )
        )

        await event.respond('Bot registered successfully')

    @match_parse('reject {bot_username}')
    async def reject_bot(self, event):
        bot_username = event.entities['bot_username']['value']
        logging.info(f"Bot {bot_username} has been rejected by admin")
        request_info = mongo_manager.get_request_by_username(bot_username)

        # register result in database
        mongo_manager.update_request_status(bot_username, 'REJECTED')

        # delete bot from marketplace!
        await self.delete_bot(event)

        # send message to request submitter to inform them that the request has been rejected
        target = request_info['request_room']
        registrar = request_info['registrar']
        await self.opsdroid.send(
            Message(
                text=f'Bad news {registrar}! your bot - '
                     f'{bot_username} - was rejected by the admin! Better luck next time!',
                target=target
            )
        )

        await event.respond('Bot rejected successfully')

    @match_parse('ban {bot_username}')
    async def ban_bot(self, event):
        bot_username = event.entities['bot_username']['value']
        logging.info(f"Bot {bot_username} has been banned by admin")
        request_info = mongo_manager.get_request_by_username(bot_username)

        # register result in database
        mongo_manager.update_request_status(bot_username, 'BANNED')

        # delete bot from marketplace!
        await self.delete_bot(event)

        # send message to request submitter to inform them that the request has been banned!
        target = request_info['request_room']
        registrar = request_info['registrar']
        await self.opsdroid.send(
            Message(
                text=f'Bad news {registrar}! your bot - '
                     f'{bot_username} - was BANNED by the admin! You can not ask for this bot to be registered again!',
                target=target
            )
        )

        await event.respond('Bot banned successfully')

    @match_parse('delete {bot_username')
    async def delete_bot(self, event):
        # this is used to remove a bot from public bots in the marketplace

        bot_username = event.entities['bot_username']['value']
        logging.info(f"Bot {bot_username} has been deleted by admin")

        # call marketplace api to remove the bot
        # TODO

        # respond with the result

    @staticmethod
    def is_username_valid(username: str):
        return bool(re.match(r"^@bot_\w+:[\w.-]+$", username))
