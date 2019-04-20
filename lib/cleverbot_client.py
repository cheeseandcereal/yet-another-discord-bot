import time
import random
import requests


class Cleverbot(object):
    """ Client for handling cleverbot.com interactions """
    def __init__(self, apikey: str, client):
        """
        Constructor for the cleverbot client

        Args:
            apikey: the apikey to use for cleverbot.com
            client: Discord client object to use with this cleverbot
        """
        self.client = client
        self.base_url = 'https://www.cleverbot.com/getreply'
        self.apikey = apikey
        self.conversations = {}
        self.timeout = 30

    async def handle_cleverbot(self, client, message, trigger_type: str, trigger: str):
        """
        Handle the cleverbot request

        Args:
            client: Discord client object
            message: Discord message object related to this request
            trigger_type: the trigger type that called this function ('author', 'first_word', or 'contains')
            trigger: the relevant string from the message that triggered this call
        """
        await self.process_request(message)

    async def process_request(self, message):
        """
        Process a request to the cleverbot api

        Args:
            message: Discord message object related of this request
        """
        await self.client.send_typing(message.channel)  # Send typing to indicate we're fetching a response
        params = {
            'input': message.content[message.content.find(' ') + 1:],
            'key': self.apikey
        }
        convo = self.conversations.get(message.channel.id)
        if(not convo or convo.get('timestamp') > time.time() + 180):  # wait 3 minutes before resetting the conversation
            print('[CLEVER_BOT] Starting new conversation')
            convo = {}
            convo['cb_settings_tweak1'] = random.randint(0, 100)
            convo['cb_settings_tweak2'] = random.randint(0, 100)
            convo['cb_settings_tweak3'] = random.randint(0, 100)
        else:
            print('[CLEVER_BOT] Continuing existing conversation')
        params['cb_settings_tweak1'] = convo['cb_settings_tweak1']
        params['cb_settings_tweak2'] = convo['cb_settings_tweak2']
        params['cb_settings_tweak3'] = convo['cb_settings_tweak3']
        params['conversation_id'] = convo.get('conversation_id')
        params['cs'] = convo.get('cs')
        # Now make the request with our params
        try:
            print('[CLEVER_BOT] {}: {}'.format(message.author.__str__(), params['input']))
            r = requests.get(url=self.base_url, params=params, timeout=self.timeout)
            # print(r.text)
            if r.status_code != 200:
                raise RuntimeError('Bad response from cleverbot: {}'.format(r.status_code))
            response = r.json(strict=False)  # Ignore possible control codes in returned data
            print(response['output'])
            # Send the response from cleverbot
            await self.client.send_message(message.channel, response['output'])
            # Now save the relevant conversation settings for future use
            convo['conversation_id'] = response['conversation_id']
            convo['cs'] = response['cs']
            convo['timestamp'] = time.time()
            self.conversations[message.channel.id] = convo
        except Exception as e:
            print('[CLEVER_BOT] Error making call: {}'.format(e))
            await self.client.send_message(message.channel, 'Sorry, I am asleep (actually I\'m probably just broken)')
