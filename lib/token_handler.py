import discord


def save_token(token):
    """
    Saves a token string to the config file
    :param token: token string to save
    :returns: Nothing
    """
    with open('config/token', 'w') as file:
        file.write('{}\n'.format(token))


def read_token():
    """
    Reads token from the saved config file
    Returns None if invalid/missing token
    :returns: token string from file or None if missing/invalid
    """
    try:
        with open('config/token', 'r') as file:
            return file.readline().rstrip()
    except Exception as e:
        print('Error while getting token: {}'.format(e))
        return None


async def validate_token(token):
    """
    Takes in a token and raises an exception if invalid
    :param token: discord authentication token for loggin in
    :returns: Nothing
    """
    client = discord.Client()
    await client.login(token)
