from typing import List, TYPE_CHECKING

if TYPE_CHECKING:
    from discord import Message
    from discord.abc import Messageable


def get_params(message: "Message") -> List[str]:
    """
    Trim the trigger word of a 'first word triggers' command and return an array of params

    Args:
        message: Discord message object to process
    Returns:
        List of whitespace seperated strings from message content
    """
    return message.content.split()[1:]


def friendly_name_of_messageable(messageable: "Messageable") -> str:
    """
    Return a string of a friendly name of a discord messageable object

    Args:
        messageable: Discord messageable object to parse
    Returns:
        String of friendly name. 'Unknown' if could not parse
    """
    friendly_name = ""
    if hasattr(messageable, "display_name"):
        friendly_name = messageable.display_name
    elif hasattr(messageable, "name"):
        friendly_name = messageable.name
    elif hasattr(messageable, "recipient"):
        friendly_name = messageable.recipient.display_name
    return friendly_name or "Unknown"
