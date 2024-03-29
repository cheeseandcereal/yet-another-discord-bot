from typing import Any, TYPE_CHECKING
import time
import os
import threading
import pickle
import asyncio
import heapq

if TYPE_CHECKING:
    from discord import Message, Client
    from discord.abc import Messageable

import discord

from lib.utils import get_params, friendly_name_of_messageable
from lib.config import get_config

usage = """```Usage: remind <user/channel> <number> <time_unit> <message>

user/channel: 'me', a mentioned user [@abc#123], 'here', or a mentioned channel [#chan]
number: integer of <time_units> before sending the reminder
time_unit: second, seconds, minute, minutes, hour, hours, day, days, week, weeks
message: message to send in the reminder```"""

offset_map = {
    "second": 1,
    "seconds": 1,
    "minute": 60,
    "minutes": 60,
    "hour": 3600,
    "hours": 3600,
    "day": 86400,
    "days": 86400,
    "week": 604800,
    "weeks": 604800,
}

lock = threading.Lock()


class RemindEvent(object):
    """Data related to a reminder event"""

    def __init__(self, user_id: int, time: float, message: str, channel_id: int = 0):
        """
        Constructor for the reminder event

        Args:
            user_id: discord user_id for this reminder
            time: unix timestamp to remind this user
            message: reminder message to send for this event
        """
        self.user_id = user_id
        self.time = time
        self.message = message
        if channel_id:
            self.channel_id = channel_id

    # Needed for heapq since it uses builtin list.sort
    def __lt__(self, other: "RemindEvent") -> bool:
        return self.time < other.time


class Reminder(object):
    """Reminder client for the bot"""

    def __init__(self, client: "Client"):
        """
        Constructor for the reminder client

        Args:
            client: Ready Discord client object
        Raises:
            RuntimeError when passed discord client is not ready
        """
        if not client.is_ready():
            raise RuntimeError("Discord client passed into Reminder client was not ready for use")
        self.client = client
        self.event_loop = asyncio.get_event_loop()
        self.save_time = int(get_config("remind_save_time"))
        self.file = os.path.join(os.getcwd(), "reminders.bin")
        # Create the reminders file if it doesn't exist
        if not os.path.exists(self.file):
            open(self.file, "a").close()
        self.init_from_file()
        self.runner = threading.Thread(target=self.thread_loop)
        self.runner.start()

    def init_from_file(self) -> None:
        """
        Read jobs from a file on initialization
        """
        f = open(self.file, "rb")
        try:
            self.jobs = pickle.load(f)
        except EOFError:
            self.jobs = []

    async def handle_remind(self, message: "Message", trigger_type: str, trigger: str) -> None:
        """
        Handle the remind request

        Args:
            message: Discord message object related to this request
            trigger_type: the trigger type that called this function ('author', 'first_word', or 'contains')
            trigger: the relevant string from the message that triggered this call
        """
        await self.process_request(message)

    async def process_request(self, message: "Message") -> Any:
        """
        Process a request for a reminder

        Args:
            message: Discord message object related to this request
        """
        params = get_params(message)
        if not params:
            return
        to_remind = params[0]
        # Parse out who to remind
        remind_user_id = 0
        remind_channel_id = 0
        # For 'me', set remind id of the message author
        if to_remind.lower() == "me":
            remind_user_id = message.author.id
        # For 'here', set remind id as channel of the message
        elif to_remind.lower() == "here":
            remind_channel_id = message.channel.id
        # For a mention, get the user/channel id
        elif "<@" in to_remind:
            # Extract just the user id
            remind_user_id = int(to_remind.replace("<@", "").replace("!", "").replace(">", ""))
        elif "<#" in to_remind:
            # Extract just the channel id
            remind_channel_id = int(to_remind.replace("<#", "").replace("!", "").replace(">", ""))
        else:  # User/channel was never set; invalid request
            msg = "Invalid <user/channel>\n" + usage
            return await message.channel.send(msg)
        # Parse out number integer
        try:
            remind_offset = int(params[1])
        except Exception:
            msg = "Invalid <number>\n" + usage
            return await message.channel.send(msg)
        # Parse out time unit
        try:
            remind_multiplier = offset_map[params[2].lower()]
        except Exception:
            msg = "Invalid <time_unit>\n" + usage
            await message.channel.send(msg)
            return
        remind_time = time.time() + (remind_offset * remind_multiplier)
        # Get the raw message after params
        raw_message = message.content[message.content.find(params[2]) + len(params[2]) :]
        with lock:
            heapq.heappush(self.jobs, RemindEvent(remind_user_id, remind_time, raw_message, remind_channel_id))
        await message.channel.send("ok")

    def thread_loop(self) -> None:
        """
        The loop for the thread that handles sending reminders
        """
        count = 0
        while True:
            try:
                time.sleep(1)
                count += 1
                while self.jobs and self.jobs[0].time < time.time():
                    with lock:
                        current = heapq.heappop(self.jobs)
                    # For backwards compatibility and reminders that don't have a channel id
                    if not hasattr(current, "channel_id"):
                        current.channel_id = 0
                    messageable: "Messageable" = None  # type: ignore
                    try:
                        if current.channel_id:
                            # We are sure this channel is messageable because it's the same channel ID where we originally received a remind message; coerce type
                            messageable = asyncio.run_coroutine_threadsafe(self.client.fetch_channel(current.channel_id), self.event_loop).result()  # type: ignore
                        else:
                            messageable = asyncio.run_coroutine_threadsafe(self.client.fetch_user(current.user_id), self.event_loop).result()
                    except discord.NotFound:
                        print(
                            "[REMINDER] WARNING: Couldn't locate {} with id {} for reminder. Ignoring this reminder (message was:{})".format(
                                "channel" if current.channel_id else "user",
                                current.channel_id if current.channel_id else current.user_id,
                                current.message,
                            )
                        )
                        continue
                    print("Sending reminder to {}".format(friendly_name_of_messageable(messageable)))
                    # Fire off reminder message when time in the main thread
                    asyncio.run_coroutine_threadsafe(messageable.send(current.message), self.event_loop)
                # Occasionally backup to disk
                if count >= self.save_time:
                    with open(self.file, "wb") as f:
                        pickle.dump(self.jobs, f)
                    count = 0
            except Exception as e:
                print("Exception in Reminder thread loop: {}".format(e))
