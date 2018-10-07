from lib.config import get_config
from lib.booru_client import handle_danr, handle_spam
import lib.misc_functions

# Make sure each of the entries in these arrays have an entry in the function_map dictionary for their relevant functions
msg_author_triggers = []
msg_contains_triggers = ['linux']
msg_first_word_triggers = ['danr', 'spam']

# Functions which handle messages taking in the params (client, message)
function_map = {
    'danr': handle_danr,
    'spam': handle_spam,
    'linux': lib.misc_functions.linux_saying
}


def add_triggers(config_entry, trigger_array):
    for item in get_config(config_entry).split(','):
        try:
            response_type = get_config(section=item, key='type')
            if response_type == 'message':
                function_map[item] = lib.misc_functions.send_simple_message
            else:
                raise RuntimeError('Response type {} not supported'.format(response_type))
            trigger_array.append(item)
        except Exception:
            print('WARNING: Error adding trigger for {}'.format(item))


add_triggers('author_triggers', msg_author_triggers)
add_triggers('contains_triggers', msg_contains_triggers)
add_triggers('first_word_triggers', msg_first_word_triggers)


async def handle_message(client, message):
    """
    Handle a discord message event
    :param client: Discord client object
    :param message: Discord message object for this event
    :returns: Nothing
    """
    # Don't let the bot trigger itself
    if message.author != client.user:
        author = message.author.__str__()
        first_word = message.content.split()[0].lower()
        if author in msg_author_triggers:
            try:
                await function_map[author](client, message, 'author', author)
            except Exception as e:
                print('WARNING: Exception thrown during author function call', e)
        if first_word in msg_first_word_triggers:
            try:
                await function_map[first_word](client, message, 'first_word', first_word)
            except Exception as e:
                print('WARNING: Exception thrown during first_word function call', e)
        for phrase in msg_contains_triggers:
            if phrase in message.content.lower():
                try:
                    await function_map[phrase](client, message, 'contains', phrase)
                except Exception as e:
                    print('WARNING: Exception thrown during contains function call', e)


async def handle_reaction_add(reaction, user):
    """
    Handle a reaction add event
    :param reaction: Discord reaction object
    :param user: Discord user object
    :returns: Nothing
    """
    pass
