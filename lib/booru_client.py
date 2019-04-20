import requests
import math
from lib.utils import get_params


async def handle_danr(message, trigger_type: str, trigger: str):
    """
    Handle the booru danr request

    Args:
        message: Discord message object related to this request
        trigger_type: the trigger type that called this function ('author', 'first_word', or 'contains')
        trigger: the relevant string from the message that triggered this call
    """
    await message.channel.trigger_typing()
    await process_request(message.channel, 1, get_params(message))


async def handle_spam(message, trigger_type, trigger):
    """
    Handle the booru spam request

    Args:
        message: Discord message object related to this request
        trigger_type: the trigger type that called this function ('author', 'first_word', or 'contains')
        trigger: the relevant string from the message that triggered this call
    """
    params = get_params(message)
    try:
        amount = int(params[0])
        if amount < 1:
            await message.channel.send(':thinking:')
            return
    except Exception:
        await message.channel.send('Usage: `spam <amount> <optional space seperated tags>`')
        return
    params = params[1:]
    await message.channel.trigger_typing()
    await process_request(message.channel, amount, params)


async def process_request(channel, amount: int, params: list):
    """
    Process a request to the booru client

    Args:
        channel: Discord channel model
        amount: Integer amount of images to request
        params: List of tags (Note: danbooru has max limit of up to 2)
    """
    warning = ''
    if amount > 200:
        warning = ':warning:Note: Danbooru doesn\'t allow requests over 200 in size. This request will be limited'
    if len(params) > 2:
        warning = ':warning:Note: Danbooru doesn\'t allow searching on more than 2 tags at once. Search will be limited to your first 2 tag'
        params = params[:2]
    if warning:
        await channel.send(warning)
    print('[BOORU_CLIENT] Request for {} images with tags: {}'.format(amount, params))
    try:
        result = get_danbooru(amount, params)
    except Exception:
        print('[BOORU_CLIENT] Request threw an exception')
        await channel.send('Error while getting content. Maybe the booru api is down or malfunctioning?')
        return
    if not result:
        print('[BOORU_CLIENT] Request had no (or bad) results')
        await channel.send('No result found. Find better tags: https://www.donmai.us/tags')
        return
    else:
        length = len(result)
        print('[BOORU_CLIENT] Sending back results: {}'.format(result))
        print('[BOORU_CLIENT] {} proper image url responses.'.format(length))
        if length > 1:
            msg = await channel.send('Retrieved {} results. Sending now'.format(length))
        for x in range(math.ceil(length / 5)):
            await channel.send('\n'.join(result[x * 5:(x * 5) + 5]))
        if length > 1:
            await channel.send('Done', delete_after=1.5)
            await msg.delete()


def get_danbooru(amount: int, tags: list):
    """
    Makes an http call to the danbooru api, returning an array of image URLs

    Args:
        amount: Integer amount of images to request
        tags: list of tags (Note: danbooru has max limit of up to 2)
    Returns:
        List of image URLs matching search with length <= amount. Empty if no results
    """
    offset = max([3, math.ceil(amount * 0.25)])
    # Request more than we need because sometimes danbooru will return bad results amidst good ones
    r = requests.get('https://danbooru.donmai.us/posts.json?tags={}&random=true&limit={}'.format('+'.join(tags), amount + offset))
    response = r.json()
    if len(response) == 0:
        print('[BOORU_CLIENT] Request had no results')
        return None
    else:
        results = []
        count = 0
        print('[BOORU_CLIENT] {} hits'.format(len(response)))
        for item in response:
            url = item.get('file_url')
            if url and (not url.endswith('.zip')):
                results.append(url)
                count += 1
                if count >= amount:
                    break
        return results
