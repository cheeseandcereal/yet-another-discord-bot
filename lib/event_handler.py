from typing import List, TYPE_CHECKING

from lib.config import get_config
from lib.booru_client import handle_danr, handle_spam
from lib.waifu_client import handle_waifu
from lib.cleverbot_client import Cleverbot
from lib.remind_client import Reminder
import lib.misc_functions

if TYPE_CHECKING:
    from discord import Message, Client, User, Reaction


class EventHandler(object):
    def initialize(self, client: "Client") -> None:
        """
        Initialize this EventHandler

        Args:
            client: Ready Discord client object
        Raises:
            RuntimeError when passed discord client is not ready
        """
        if not client.is_ready():
            raise RuntimeError("Discord client passed into EventHandler was not ready for use")
        self.client = client
        # Make sure each of the entries in these arrays have an entry in the function_map dictionary for their relevant functions
        self.msg_author_triggers: List[str] = []
        self.msg_contains_triggers: List[str] = []
        self.msg_first_word_triggers = ["danr", "spam", "choose", "waifu", "imouto", "oneechan", "oneesan"]
        if get_config("linux_nag") == "true":
            self.msg_contains_triggers.append("linux")

        # Functions which handle messages taking in the params (client, message)
        self.function_map = {
            "danr": handle_danr,
            "spam": handle_spam,
            "linux": lib.misc_functions.linux_saying,
            "choose": lib.misc_functions.handle_choose,
            "waifu": handle_waifu,
            "imouto": handle_waifu,
            "oneechan": handle_waifu,
            "oneesan": handle_waifu,
        }

        try:
            if get_config("cleverbot_integration") == "true":
                self.clever = Cleverbot(get_config("cleverbot_api_key"))
                self_mention_1 = "<@!{}>".format(self.client.user.id)
                self_mention_2 = "<@{}>".format(self.client.user.id)
                self.msg_first_word_triggers.append(self_mention_1)
                self.msg_first_word_triggers.append(self_mention_2)
                self.function_map[self_mention_1] = self.clever.handle_cleverbot
                self.function_map[self_mention_2] = self.clever.handle_cleverbot
        except Exception:
            print("WARNING: Error processing cleverbot integration")

        try:
            if get_config("remind_enabled") == "true":
                self.remind = Reminder(self.client)
                self.msg_first_word_triggers.append("remind")
                self.function_map["remind"] = self.remind.handle_remind
        except Exception:
            print("WARNING: Error processing reminder integration")

        self.add_triggers("author_triggers", self.msg_author_triggers)
        self.add_triggers("contains_triggers", self.msg_contains_triggers)
        self.add_triggers("first_word_triggers", self.msg_first_word_triggers)

    def add_triggers(self, config_entry: str, trigger_array: List[str]) -> None:
        """
        Read bot triggers from a settings configuration entry and make them active for the bot

        Args:
            config_entry: settings config key of the entries to read
            trigger_array: list to add the parsed triggers into
        """
        for item in get_config(config_entry).split(","):
            try:
                response_type = get_config(section=item, key="type")
                if response_type == "message":
                    self.function_map[item] = lib.misc_functions.send_simple_message
                else:
                    raise RuntimeError("Response type {} not supported".format(response_type))
                trigger_array.append(item)
            except Exception:
                print("WARNING: Error adding trigger for {}".format(item))

    async def handle_message(self, message: "Message") -> None:
        """
        Handle a discord message event

        Args:
            message: Discord message object for this event
        """
        # Don't let the bot trigger itself
        if message.author != self.client.user:
            author = message.author.__str__()
            first_word = ""
            message_parts = message.content.split()
            if message_parts:
                first_word = message_parts[0].lower()
            if author in self.msg_author_triggers:
                try:
                    await self.function_map[author](message, "author", author)
                except Exception as e:
                    print("WARNING: Exception thrown during author function call", e)
            if first_word in self.msg_first_word_triggers:
                try:
                    await self.function_map[first_word](message, "first_word", first_word)
                except Exception as e:
                    print("WARNING: Exception thrown during first_word function call", e)
            for phrase in self.msg_contains_triggers:
                if phrase in message.content.lower():
                    try:
                        await self.function_map[phrase](message, "contains", phrase)
                    except Exception as e:
                        print("WARNING: Exception thrown during contains function call", e)

    async def handle_reaction_add(self, reaction: "Reaction", user: "User") -> None:
        """
        Handle a reaction add event

        Args:
            reaction: Discord reaction object
            user: Discord user object
        """
        pass
