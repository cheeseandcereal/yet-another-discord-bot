import time
import os
import threading
import pickle
import asyncio
import heapq
from lib.utils import get_params
from lib.config import get_config

usage = """```Usage: remind <user> <number> <time_unit> <message>

user: 'me' or a mentioned user
number: integer of <time_units> before sending the reminder
time_unit: second, seconds, minute, minutes, hour, hours, day, days, week, weeks
message: message to send in the reminder```"""

offset_map = {
    'second': 1,
    'seconds': 1,
    'minute': 60,
    'minutes': 60,
    'hour': 3600,
    'hours': 3600,
    'day': 86400,
    'days': 86400,
    'week': 604800,
    'weeks': 604800
}

lock = threading.Lock()


class RemindEvent(object):
    """ Data related to a reminder event """
    def __init__(self, user, time: float, message: str):
        """
        Constructor for the reminder event

        Args:
            user: Discord user object for this reminder
            time: unix timestamp to remind this user
            message: reminder message to send for this event
        """
        self.user = user
        self.time = time
        self.message = message

    # Needed for heapq since it uses builtin list.sort
    def __lt__(self, other):
        return self.time < other.time


class Reminder(object):
    """ Reminder client for the bot """
    def __init__(self, client):
        """
        Constructor for the reminder client

        Args:
            client: Discord client object to use in order to send reminder messages
        """
        self.client = client
        self.event_loop = asyncio.get_event_loop()
        self.save_time = int(get_config('remind_save_time'))
        self.file = os.path.join(os.getcwd(), 'reminders.bin')
        # Create the reminders file if it doesn't exist
        if not os.path.exists(self.file):
            open(self.file, 'a').close()
        self.init_from_file()
        self.runner = threading.Thread(target=self.thread_loop)
        self.runner.start()

    def init_from_file(self):
        """
        Read jobs from a file on initialization
        """
        f = open(self.file, 'rb')
        try:
            self.jobs = pickle.load(f)
        except EOFError:
            self.jobs = []

    async def handle_remind(self, client, message, trigger_type: str, trigger: str):
        """
        Handle the remind request

        Args:
            client: Discord client object
            message: Discord message object related to this request
            trigger_type: the trigger type that called this function ('author', 'first_word', or 'contains')
            trigger: the relevant string from the message that triggered this call
        """
        await self.process_request(message)

    async def process_request(self, message):
        """
        Process a request for a reminder

        Args:
            message: Discord message object related to this request
        """
        params = get_params(message)
        to_remind = params[0]
        # Parse out who to remind
        remind_user = None
        # For 'me', set remind user as author
        if to_remind.lower() == 'me':
            remind_user = message.author
        # For a mention, get the user object
        else:
            # Extract just the user id from the mentions
            to_remind = to_remind.replace('<@', '').replace('!', '').replace('>', '')
            for user in message.mentions:
                if user.id == to_remind:
                    remind_user = user
            if remind_user is None:  # User was never set; invalid request
                msg = 'Invalid <user>\n' + usage
                return await self.client.send_message(message.channel, msg)
        # Parse out number integer
        try:
            remind_offset = int(params[1])
        except Exception:
            msg = 'Invalid <number>\n' + usage
            return await self.client.send_message(message.channel, msg)
        # Parse out time unit
        try:
            remind_multiplier = offset_map[params[2].lower()]
        except Exception:
            msg = 'Invalid <time_unit>\n' + usage
            return await self.client.send_message(message.channel, msg)
        remind_time = time.time() + (remind_offset * remind_multiplier)
        # Get the raw message after params
        raw_message = message.content[message.content.find(params[2]) + len(params[2]):]
        with lock:
            heapq.heappush(self.jobs, RemindEvent(remind_user, remind_time, raw_message))
        await self.client.send_message(message.channel, 'ok')

    def thread_loop(self):
        """
        The loop for the thread that handles sending reminders
        """
        count = 0
        while True:
            try:
                time.sleep(2)
                count += 2
                while self.jobs and self.jobs[0].time < time.time():
                    with lock:
                        current = heapq.heappop(self.jobs)
                    print('Sending reminder to {}'.format(current.user.display_name))
                    # Fire off reminder message when time in the main thread
                    asyncio.run_coroutine_threadsafe(self.client.send_message(current.user, current.message), self.event_loop)
                # Occasionally backup to disk
                if count >= self.save_time:
                    with open(self.file, 'wb') as f:
                        pickle.dump(self.jobs, f)
                    count = 0
            except Exception as e:
                print('Exception in Reminder thread loop {}'.format(e))
