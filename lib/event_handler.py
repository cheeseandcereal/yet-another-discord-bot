from lib.config import get_config
from lib.booru_client import handle_danr, handle_spam
from lib.cleverbot_client import Cleverbot
import lib.misc_functions


class EventHandler:
    def initialize(self, client):
        """
        Initialize this EventHandler with a fully ready client.
        This is needed because the discord client must be fully initialized before calling.
        :param client: Ready Discord client object
        :returns: Nothing
        """
        self.client = client
        # Make sure each of the entries in these arrays have an entry in the function_map dictionary for their relevant functions
        self.msg_author_triggers = []
        self.msg_contains_triggers = ['linux']
        self.msg_first_word_triggers = ['danr', 'spam', 'choose']

        # Functions which handle messages taking in the params (client, message)
        self.function_map = {
            'danr': handle_danr,
            'spam': handle_spam,
            'linux': lib.misc_functions.linux_saying,
            'choose': lib.misc_functions.handle_choose
        }

        try:
            if get_config('cleverbot_integration') == 'true':
                self.clever = Cleverbot(get_config('cleverbot_api_key'), self.client)
                self_mention = '<@{}>'.format(client.user.id)
                self.msg_first_word_triggers.append(self_mention)
                self.function_map[self_mention] = self.clever.handle_cleverbot
        except Exception:
            print('WARNING: Error processing cleverbot integration')

        self.add_triggers('author_triggers', self.msg_author_triggers)
        self.add_triggers('contains_triggers', self.msg_contains_triggers)
        self.add_triggers('first_word_triggers', self.msg_first_word_triggers)

    def add_triggers(self, config_entry, trigger_array):
        for item in get_config(config_entry).split(','):
            try:
                response_type = get_config(section=item, key='type')
                if response_type == 'message':
                    self.function_map[item] = lib.misc_functions.send_simple_message
                else:
                    raise RuntimeError('Response type {} not supported'.format(response_type))
                trigger_array.append(item)
            except Exception:
                print('WARNING: Error adding trigger for {}'.format(item))

    async def handle_message(self, message):
        """
        Handle a discord message event
        :param client: Discord client object
        :param message: Discord message object for this event
        :returns: Nothing
        """
        # Don't let the bot trigger itself
        if message.author != self.client.user:
            author = message.author.__str__()
            first_word = message.content.split()[0].lower()
            if author in self.msg_author_triggers:
                try:
                    await self.function_map[author](self.client, message, 'author', author)
                except Exception as e:
                    print('WARNING: Exception thrown during author function call', e)
            if first_word in self.msg_first_word_triggers:
                try:
                    await self.function_map[first_word](self.client, message, 'first_word', first_word)
                except Exception as e:
                    print('WARNING: Exception thrown during first_word function call', e)
            for phrase in self.msg_contains_triggers:
                if phrase in message.content.lower():
                    try:
                        await self.function_map[phrase](self.client, message, 'contains', phrase)
                    except Exception as e:
                        print('WARNING: Exception thrown during contains function call', e)

    async def handle_reaction_add(self, reaction, user):
        """
        Handle a reaction add event
        :param reaction: Discord reaction object
        :param user: Discord user object
        :returns: Nothing
        """
        pass
