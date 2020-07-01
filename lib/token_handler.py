from typing import Union

import discord


def save_token(token: str) -> None:
    """
    Saves a token string to the config file

    Args:
        token: token string to save
    """
    with open("config/token", "w") as file:
        file.write("{}\n".format(token))


def read_token() -> Union[str, None]:
    """
    Reads token from the saved config file

    Returns:
        token string from file (or None if missing/invalid)
    """
    try:
        with open("config/token", "r") as file:
            return file.readline().rstrip()
    except Exception as e:
        print("Error while getting token: {}".format(e))
        return None


async def validate_token(token: str) -> None:
    """
    Checks a discord token by raising an exception if invalid

    Args:
        token: discord authentication token for loggin in
    """
    client = discord.Client()
    await client.login(token)
