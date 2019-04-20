import random
from lib.config import get_config
from lib.utils import get_params


async def add_random_reaction(client, message):
    """
    Add a reaction sequence to a message

    Args:
        client: Discord client object
        message: Relevant discord message object to add reactions for
    """
    reaction = random.choice(get_config('random_reaction_values').split(','))
    for char in reaction:
        await client.add_reaction(message, char)


async def send_simple_message(client, message, trigger_type: str, trigger: str):
    """
    Send a simple message response

    Args:
        client: Discord client object
        message: Discord message object related to this request
        trigger_type: the trigger type that called this function ('author', 'first_word', or 'contains')
        trigger: the relevant string from the message that triggered this call
    """
    msg = get_config(section=trigger, key='message')
    await client.send_message(message.channel, msg)


async def linux_saying(client, message, trigger_type: str, trigger: str):
    """
    Check if 'linux' was said in the context of 'gnu/linux' and send a message if not 'gnu/linux'

    Args:
        client: Discord client object
        message: Discord message object related to this request
        trigger_type: the trigger type that called this function ('author', 'first_word', or 'contains')
        trigger: the relevant string from the message that triggered this call
    """
    msg = message.content.lower()
    # First find all the indices where the string 'linux' occurs
    curr = msg.find('linux')
    indices = []
    while curr != -1:
        indices.append(curr)
        curr = msg.find('linux', curr + 5)
    # Check all occurrences of 'linux' for preceding 'gnu/' or 'gnu plus '
    send_message = False
    for i in indices:
        # Edge case if linux appears too far forward in the string
        # (gnu/ can't possibly exist in front)
        if i < 4:
            send_message = True
            break
        check = False
        if i >= 4:
            check = check or msg[i - 4:i] == 'gnu/'
        if i >= 9:
            check = check or msg[i - 9:i] == 'gnu plus '
        if not check:
            send_message = True
            break
    if send_message:
        await client.send_message(message.channel, "I'd just like to interject for moment. What you're refering to as Linux, is in fact, GNU/Linux, or as I've recently taken to calling it, GNU plus Linux. Linux is not an operating system unto itself, but rather another free component of a fully functioning GNU system made useful by the GNU corelibs, shell utilities and vital system components comprising a full OS as defined by POSIX.\nMany computer users run a modified version of the GNU system every day, without realizing it. Through a peculiar turn of events, the version of GNU which is widely used today is often called Linux, and many of its users are not aware that it is basically the GNU system, developed by the GNU Project.\nThere really is a Linux, and these people are using it, but it is just a part of the system they use. Linux is the kernel: the program in the system that allocates the machine's resources to the other programs that you run. The kernel is an essential part of an operating system, but useless by itself; it can only function in the context of a complete operating system. Linux is normally used in combination with the GNU operating system: the whole system is basically GNU with Linux added, or GNU/Linux. All the so-called Linux distributions are really distributions of GNU/Linux!")


async def handle_choose(client, message, trigger_type: str, trigger: str):
    """
    Handler to pick a random word from a message

    Args:
        client: Discord client object
        message: Discord message object related to this request
        trigger_type: the trigger type that called this function ('author', 'first_word', or 'contains')
        trigger: the relevant string from the message that triggered this call
    """
    options = get_params(message)
    await client.send_message(message.channel, random.choice(options))
