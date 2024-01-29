from opsdroid.skill import Skill
from opsdroid.matchers import match_event, match_crontab, match_parse
from opsdroid.events import Message, JoinRoom, UserInvite, LeaveRoom
import logging


class AcceptDirectMessageSkill(Skill):
    @match_parse('hi')
    async def accept_direct_message(self, event):
        logging.info(f"GREET -> {event}")
        response = "Hi! I'm bot father! I'm here to help you register and manage your bots!"
        await event.respond(response)
