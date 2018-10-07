def get_params(message):
    """
    Trim the trigger word of a 'first word triggers' command and return an array of params
    :param message: Discord message object to process
    :returns: Array of whitespace seperated strings from message content
    """
    return message.content.split()[1:]
