from telegram.ext import BaseFilter

class InGroupFilter(BaseFilter):
    def filter(self, message):
        return message.chat.type == 'group' or message.chat.type == 'supergroup'

class RedditFilter(BaseFilter):
    def filter(self, message):
        return message.text is not None and '/r/' in message.text

class MentionFilter(BaseFilter):
    def filter(self, message):
        return message.text is not None and '@Sn0wBit2_bot' in message.text

class UserAddedFilter(BaseFilter):
    def filter(self, message):
        return len(message.new_chat_members) > 0

class UserLeftFilter(BaseFilter):
    def filter(self, message):
        return message.left_chat_member is not None

class PrivateMessageFilter(BaseFilter):
    def filter(self, message):
        return message.from_user.id == message.chat_id

class InsultingWorldFilter(BaseFilter):
    def filter(self, message):
        if message.text is not None:
            insulting_words = ["kys", "faggot", "stupid", "aids", "whore", "eat me", "suicide"]
            return any(word in message.text for word in insulting_words) and '@Sn0wBit2_bot' in message.text
        else:
            return False

class NoUFilter(BaseFilter):
    def filter(self, message):
        if message.text is not None:
            return 'no u' in message.text or 'No u' in message.text or 'NO U' in message.text
        else:
            return False

class ClearFilter(BaseFilter):
    def filter(self, message):
        return message.text is not None and message.text == "clear"
