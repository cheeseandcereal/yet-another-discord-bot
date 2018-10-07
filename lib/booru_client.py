import requests
import time
import math
from lib.utils import get_params


async def handle_danr(client, message, trigger_type, trigger):
    """
    Handle the booru danr request
    :param client: Discord client object
    :param message: Discord message object related to this request
    :returns: Nothing
    """
    await process_request(client, message.channel, 1, get_params(message))


async def handle_spam(client, message, trigger_type, trigger):
    """
    Handle the booru spam request
    :param client: Discord client object
    :param message: Discord message object related to this request
    :returns: Nothing
    """
    params = get_params(message)
    try:
        amount = int(params[0])
        if amount < 1:
            await client.send_message(message.channel, ':warning:Warning: Retard alert:triumph:')
            return
    except Exception:
        await client.send_message(message.channel, 'Usage: `spam <amount> <optional space seperated tags>`')
        return
    params = params[1:]
    await process_request(client, message.channel, amount, params)


async def process_request(client, channel, amount, params):
    """
    Process a request to the booru client
    :param client: Discord client object
    :param channel: Channel to send the messages to
    :param amount: Integer amount of images to request
    :param params: Array of tags (Note: danbooru has max limit of up to 2)
    :returns: Nothing
    """
    warning = ''
    if amount > 200:
        warning = ':warning:Note: Danbooru doesn\'t allow requests over 200 in size. This request will be limited'
    if len(params) > 2:
        warning = ':warning:Note: Danbooru doesn\'t allow searching on more than 2 tags at once. Search will be limited to your first 2 tag'
        params = params[:2]
    if warning:
        await client.send_message(channel, warning)
    msg = await client.send_message(channel, 'Fetching Images...')
    print('[BOORU_CLIENT] Request for {} images with tags: {}'.format(amount, params))
    try:
        result = get_danbooru(amount, params)
    except Exception:
        print('[BOORU_CLIENT] Request threw an exception')
        await client.edit_message(msg, 'Error while getting content. Maybe the booru api is down or malfunctioning?')
    if not result:
        print('[BOORU_CLIENT] Request had no (or bad) results')
        await client.edit_message(msg, 'No result found. Find better tags: https://www.donmai.us/tags')
    else:
        length = len(result)
        print('[BOORU_CLIENT] Sending back results: {}'.format(result))
        print('[BOORU_CLIENT] {} proper image url responses.'.format(length))
        if length > 1:
            await client.edit_message(msg, 'Retrieved {} results. Sending now'.format(length))
        else:
            await client.delete_message(msg)
        for x in range(math.ceil(length / 5)):
            await client.send_message(channel, '\n'.join(result[x * 5:(x * 5) + 5]))
        if length > 1:
            done = await client.send_message(channel, 'Done')
            await client.delete_message(msg)
            time.sleep(1)
            await client.delete_message(done)


def get_danbooru(amount, tags):
    """
    Makes an http call to the danbooru api, returning an array of image URLs
    :param amount: Integer amount of images to request
    :param tags: Array of tags (Note: danbooru has max limit of up to 2)
    :returns: Array of image URLs matching search with length <= amount. Empty if no results
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
