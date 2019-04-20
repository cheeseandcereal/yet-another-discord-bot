from bs4 import BeautifulSoup
import requests

error_message = 'There was an error fetching a waifu! Sorry!'


async def handle_waifu(message, trigger_type: str, trigger: str):
    """
    Handle the waifu request

    Args:
        message: Discord message object related to this request
        trigger_type: the trigger type that called this function ('author', 'first_word', or 'contains')
        trigger: the relevant string from the message that triggered this call
    """
    await message.channel.trigger_typing()
    await process_request(message.channel, trigger)


async def process_request(channel, trigger: str):
    """
    Process a request to deal with the waifu request

    Args:
        channel: Discord channel object to send the response
        trigger: trigger word for this request
    """
    r = requests.get('https://mywaifulist.moe/random')
    # Handle bad response
    if r.status_code < 200 or r.status_code >= 300:
        await channel.send(error_message)
        print('Warning: Response {} from mywaifulist'.format(r.status_code))
        print(r.text)
        return
    try:
        # Parse html for the waifu id
        page = BeautifulSoup(r.text, 'html.parser')
        waifu_id = page.find('waifu-core').get(':waifu-id')
        # Now query the api for the waifu information
        r = requests.get('https://mywaifulist.moe/api/waifu/{}'.format(waifu_id), headers={'X-Requested-With': 'XMLHttpRequest'})
        if r.status_code < 200 or r.status_code >= 300:
            await channel.send(error_message)
            print('Warning: Response {} from mywaifulist api'.format(r.status_code))
            print(r.text)
            return
        print(r.text)
        res = r.json()
        await channel.send('Your {} is {} from {}\n{}'.format(trigger, res['name'], res['series']['name'], res['display_picture']))
        # Make sure to truncate the descripiton if it is too long for discord
        if len(res['description']) >= 1950:
            res['description'] = res['description'][:1950] + '...'
        await channel.send(res['description'])
    except Exception as e:
        print(e)
        await channel.send(error_message)
