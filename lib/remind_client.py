import time
import os
import threading
import pickle
import asyncio
import heapq
from lib.utils import get_params

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


class RemindEvent:
    def __init__(self, user, time, message):
        self.user = user
        self.time = time
        self.message = message

    # Needed for heapq since it uses builtin list.sort
    def __lt__(self, other):
        return self.time < other.time


class Reminder:
    def __init__(self, client):
        self.client = client
        self.event_loop = asyncio.get_event_loop()
        self.file = os.path.join(os.getcwd(), 'reminders.bin')
        if(not os.path.exists(self.file)):
            open(self.file, 'a').close()
        self.init_from_file()
        self.runner = threading.Thread(target=self.thread_loop)
        self.runner.start()

    def init_from_file(self):
        """
        Read jobs from a file on initialization
        :returns: Nothing
        """
        f = open(self.file, 'rb')
        try:
            self.jobs = pickle.load(f)
        except EOFError:
            self.jobs = []

    async def handle_remind(self, client, message, trigger_type, trigger):
        """
        Handle the remind request
        :param client: Discord client object
        :param message: Discord message object related to this request
        :returns: Nothing
        """
        await self.process_request(message)

    async def process_request(self, message):
        """
        Process a request for a reminder
        :param message: Message of this request
        :returns: Nothing
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
            # Extract just the user id
            to_remind = to_remind.replace('<@', '')
            to_remind = to_remind.replace('!', '')
            to_remind = to_remind.replace('>', '')
            for user in message.mentions:
                if user.id == to_remind:
                    remind_user = user
            if remind_user is None:  # User was never set; invalid request
                msg = 'Invalid <user>\n' + usage
                await self.client.send_message(message.channel, msg)
                return
        # Parse out number integer
        try:
            remind_offset = int(params[1])
        except Exception:
            msg = 'Invalid <number>\n' + usage
            await self.client.send_message(message.channel, msg)
            return
        # Parse out time unit
        try:
            remind_multiplier = offset_map[params[2].lower()]
        except Exception:
            msg = 'Invalid <time_unit>\n' + usage
            await self.client.send_message(message.channel, msg)
            return
        remind_time = time.time() + (remind_offset * remind_multiplier)
        # Get the raw message after params
        raw_message = message.content[message.content.find(params[2]) + len(params[2]):]
        heapq.heappush(self.jobs, RemindEvent(remind_user, remind_time, raw_message))
        await self.client.send_message(message.channel, 'ok')

    def thread_loop(self):
        """
        The loop for the thread that handles sending reminders
        """
        count = 1
        while(True):
            try:
                time.sleep(2)
                while(self.jobs and self.jobs[0].time < time.time()):
                    current = heapq.heappop(self.jobs)
                    print('Sending reminder to {}'.format(current.user.display_name))
                    asyncio.run_coroutine_threadsafe(self.client.send_message(current.user, current.message), self.event_loop)
                # Occasionally backup to disk
                if count % 7 == 0:
                    f = open(self.file, 'wb')
                    pickle.dump(self.jobs, f)
                    f.close()
                count += 1
            except Exception as e:
                print('Exception in Reminder thread loop {}'.format(e))
