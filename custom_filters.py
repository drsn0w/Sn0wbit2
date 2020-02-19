from telegram.ext import BaseFilter

class RedditFilter(BaseFilter):
    def filter(self, message):
        return '/r/' in message.text

class MentionFilter(BaseFilter):
    def filter(self, message):
        return '@Sn0wBit2_bot' in message.text

class UserAddedFilter(BaseFilter):
    def filter(self, message):
        return message.new_chat_members is not None

class UserLeftFilter(BaseFilter):
    def filter(self, message):
        return message.left_chat_member is not None

class InGroupFilter(BaseFilter):
    def filter(self, message):
        return message.from_user.id != message.chat_id

class PrivateMessageFilter(BaseFilter):
    def filter(self, message):
        return message.from_user.id == message.chat_id

class InsultingWorldFilter(BaseFilter):
    def filter(self, message):
        insulting_words = ["kys", "faggot", "stupid", "aids", "whore", "eat me", "suicide"]
        return any(word in message.text for word in insulting_words) and '@Sn0wBit2_bot' in message.text

class NoUFilter(BaseFilter):
    def filter(self, message):
        return 'no u' in message.text or 'No u' in message.text or 'NO U' in message.text

class ClearFilter(BaseFilter):
    def filter(self, message):
        return message.text == "clear"
