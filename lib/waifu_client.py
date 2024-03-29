# WARNING: This integration currently does not work due to anti-bot scraping protections by mywaifulist
# It would be possible to fix this integration with paid API access/integration in the future
from typing import TYPE_CHECKING

from bs4 import BeautifulSoup
import requests

if TYPE_CHECKING:
    from discord import Message
    from discord.abc import MessageableChannel

error_message = "There was an error fetching a waifu! Sorry!"


async def handle_waifu(message: "Message", trigger_type: str, trigger: str) -> None:
    """
    Handle the waifu request

    Args:
        message: Discord message object related to this request
        trigger_type: the trigger type that called this function ('author', 'first_word', or 'contains')
        trigger: the relevant string from the message that triggered this call
    """
    await message.channel.typing()
    await process_request(message.channel, trigger)


async def process_request(channel: "MessageableChannel", trigger: str) -> None:
    """
    Process a request to deal with the waifu request

    Args:
        channel: Discord channel object to send the response
        trigger: trigger word for this request
    """
    # Python do-while. Will return out of loop when necessary
    while True:
        r = requests.get("https://mywaifulist.moe/random")
        # Handle bad response
        if r.status_code < 200 or r.status_code >= 300:
            await channel.send(error_message)
            print("Warning: Response {} from mywaifulist".format(r.status_code))
            print(r.text)
            return
        try:
            # Parse html for the waifu id
            page = BeautifulSoup(r.text, "html.parser")
            waifu_id = page.find("waifu-core").get(":waifu-id")
            # Now query the api for the waifu information
            r = requests.get("https://mywaifulist.moe/api/waifu/{}".format(waifu_id), headers={"X-Requested-With": "XMLHttpRequest"})
            if r.status_code < 200 or r.status_code >= 300:
                await channel.send(error_message)
                print("Warning: Response {} from mywaifulist api".format(r.status_code))
                print(r.text)
                return
            print(r.text)
            res = r.json()
            # If result is a husbando, ignore this request and try again
            if res["data"].get("husbando"):
                continue
            await channel.send(
                "Your {} is {} from {}\n{}".format(trigger, res["data"]["name"], res["data"]["series"]["name"], res["data"]["display_picture"])
            )
            # Make sure to truncate the descripiton if it is too long for discord
            if len(res["data"]["description"]) >= 1950:
                res["data"]["description"] = res["data"]["description"][:1950] + "..."
            await channel.send(res["data"]["description"])
            return
        except Exception as e:
            print(e)
            await channel.send(error_message)
            return
