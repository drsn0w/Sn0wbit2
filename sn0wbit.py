import sys
import logging
import threading
from urllib.request import urlopen
from urllib import error as u_error
# Reddit Filter
import custom_filters as CustomFilters
import nltext
import markov_tools
# Import telegram
import telegram
from telegram.ext import Updater
from telegram.ext import CommandHandler
from telegram.ext import MessageHandler,Filters
#markov
import markovify
import configparser as ConfigParser

# CONFIGURATION OPTIONS
CFG_TELEGRAM_API_KEY = ""
CFG_MARKOV_CHAIN_NAME = ""
CFG_SUPER_USER_ID = 0
CFG_ORIGINAL_OVERLAP = 0
CFG_TRAINING_LOCKED = False

# MODEL TRAINING LOCK
TRAIN_LOCK = threading.Lock()

# Processing subroutines
# Naming follows this convention:
# t_ : text match
# c_ : command match
# a_ : action match

# Parses out subreddits and posts a link to them
def t_reddit(bot, update):
    # make text a bit more accessible
    m_text = update.message.text
    # Split message into words
    words = m_text.split()
    parsed_one = False
    for word in words:
        # If the message contains '/r/' and we have not already found a subreddit
        if "/r/" in word and not parsed_one:
            # form the URL
            r_url = "https://reddit.com" + word
            # Check if it's actually a subreddit
            try:
                u_result = urlopen(r_url)
                if u_result.code == 200:
                    # If it is, paste the link
                    bot.sendMessage(chat_id=update.message.chat_id, text="https://reddit.com" + word)
                    parsed_one = True
            except u_error.HTTPError as err:
                if err.code == 404:
                    bot.sendMessage(chat_id=update.message.chat_id, text="That subreddit does not exist!")
                    parsed_one = True
                elif err.code == 427:
                    bot.sendMessage(chat_id=update.message.chat_id, text="You are sending too many requests!")
                    parsed_one = True

# A plesant placeholder message
def c_start(bot, update):
    bot.sendMessage(chat_id=update.message.chat_id, text="Fuck off, " + update.message.from_user.first_name + "!")

# Echos text back in PMs
def t_echo(bot, update):
    # Make some frequently used things more accessible
    s_first_name = update.message.from_user.first_name
    s_user_id = update.message.from_user.id
    s_chat_id = update.message.chat_id

    # Don't echo in group chats
    if s_user_id == s_chat_id:
        # Make sure Basil isn't abusing the bot
        if s_first_name == "Basil":
            bot.sendMessage(chat_id=update.message.chat_id, text="Suck a dick.")
        else:
            bot.sendMessage(chat_id=update.message.chat_id, text=update.message.text)

# Creates silly responses based on markov chains!
def t_markov(bot, update):
    try:
        with open("./" + CFG_MARKOV_CHAIN_NAME + ".train.mchain") as f:
            text = f.read()

        text_model = markovify.NewlineText.from_chain(text)
        s_starting_word = markov_tools.get_random_starting_word(text_model)
        #bot.sendMessage(chat_id=update.message.chat_id, text="DEGUB: " + s_starting_word)
        s_sentence = text_model.make_short_sentence(240, max_overlap_ratio=CFG_ORIGINAL_OVERLAP)
        if s_sentence is None:
            bot.sendMessage(chat_id=update.message.chat_id, text=markov_tools.humanize(s_starting_word))
        else:
            bot.sendMessage(chat_id=update.message.chat_id, text=markov_tools.humanize(s_sentence))
    except FileNotFoundError:
        bot.sendMessage(chat_id=update.message.chat_id, text="Speech model does not exist!")

# Greets a user
def a_useradd(bot, update):
    for newuser in update.message.new_chat_members:
        fname = newuser.first_name
        bot.sendMessage(chat_id=update.message.chat_id, text="Welcome, " + fname + "!")


# Says goodbye to a user
def a_userleft(bot, update):
    fname = update.message.left_chat_member.first_name
    bot.sendMessage(chat_id=update.message.chat_id, text="Goodbye, " + fname + "!")

# Trains the chat model based on chat messages longer than one words
def t_train(bot, update):
    # Spawn a new thread to append the message to the chat model
    train_thread = threading.Thread(target = append_chat_model, args = (update, ))
    train_thread.start()

# Trains the chat model based on a given telegram Update
def append_chat_model(update):
    # Spin until we can acquire the TRAIN_LOCK
    TRAIN_LOCK.acquire(blocking=True)

    if not CFG_TRAINING_LOCKED:
        # Make text easily accessible
        message_text = update.message.text
        m_text_words = message_text.split()
        if len(m_text_words) > 0:
            # Append message to record:
            train_text = message_text.replace("\"", "").replace("\'", "")
            with open(CFG_MARKOV_CHAIN_NAME + ".train", "a") as chat_file:
                chat_file.write(markov_tools.botify(train_text) + "\n")
            # Regenerate training model based on natural language
            markov_tools.regenerate_model(CFG_MARKOV_CHAIN_NAME +".train")

    # Release the lock now that we're done
    TRAIN_LOCK.release()

# Manually retrain the speech model
def c_manualretrain(bot, update):
    sender_id = update.message.from_user.id
    if sender_id != CFG_SUPER_USER_ID:
        bot.sendMessage(chat_id=update.message.chat_id, text="You are not an administrator!")
    else:
        try:
            markov_tools.regenerate_model(CFG_MARKOV_CHAIN_NAME +".train")
            bot.sendMessage(chat_id=update.message.chat_id, text="Speech model regenerated!")
        except FileNotFoundError:
            bot.sendMessage(chat_id=update.message.chat_id, text="Speech model does not exist!")

# Reset the speech model
def c_resetmodel(bot, update):
    sender_id = update.message.from_user.id
    if sender_id != CFG_SUPER_USER_ID:
        bot.sendMessage(chat_id=update.message.chat_id, text="You are not an administrator!")
    else:
        markov_tools.reset_model(CFG_MARKOV_CHAIN_NAME +".train")
        bot.sendMessage(chat_id=update.message.chat_id, text="Speech model reset!")

# List top 10 starting words in speech model (CURRENTLY BROKEN)
def c_startingwords(bot, update):
    sender_id = update.message.from_user.id
    if sender_id != CFG_SUPER_USER_ID:
        bot.sendMessage(chat_id=update.message.chat_id, text="You are not an administrator!")
    else:
        try:
            with open(CFG_MARKOV_CHAIN_NAME +".train.mchain") as f:
                text = f.read()

            text_model = markovify.NewlineText.from_json(text)
            only_starting_words = markov_tools.get_starting_words(text_model)
            bot.sendMessage(chat_id=update.message.chat_id, text=only_starting_words)
        except FileNotFoundError:
            bot.sendMessage(chat_id=update.message.chat_id, text="Speech model does not exist!")

# Changes speech model from a chat command MAKE PERSISTENT
def c_changespeechmodel(bot, update):
    sender_id = update.message.from_user.id
    if sender_id != CFG_SUPER_USER_ID:
        bot.sendMessage(chat_id=update.message.chat_id, text="You are not an administrator!")
    else:
        message_text = update.message.text
        message_words = message_text.split()
        message_length = len(message_words)
        if message_length != 2:
            bot.sendMessage(chat_id=update.message.chat_id, text="Usage: /changespeechmodel [model name]")
        else:
            global CFG_MARKOV_CHAIN_NAME
            CFG_MARKOV_CHAIN_NAME = message_words[1]
            bot.sendMessage(chat_id=update.message.chat_id, text="Speech model changed to " + message_words[1] + "!")

# Stops bot from training based on chat messages
def c_locktraining(bot, update):
    sender_id = update.message.from_user.id
    if sender_id != CFG_SUPER_USER_ID:
        bot.sendMessage(chat_id=update.message.chat_id, text="You are not an administrator!")
    else:
        global CFG_TRAINING_LOCKED
        CFG_TRAINING_LOCKED = True
        bot.sendMessage(chat_id=update.message.chat_id, text="Training locked!")

# Allows bot to be trained from chat messages
def c_unlocktraining(bot, update):
    sender_id = update.message.from_user.id
    if sender_id != CFG_SUPER_USER_ID:
        bot.sendMessage(chat_id=update.message.chat_id, text="You are not an administrator!")
    else:
        global CFG_TRAINING_LOCKED
        CFG_TRAINING_LOCKED = False
        bot.sendMessage(chat_id=update.message.chat_id, text="Training unlocked!")

# Displays a status message
def c_displaystatus(bot, update):
    status_message = "*Current Settings*"
    status_message += "\n*Speech Model:* " + CFG_MARKOV_CHAIN_NAME
    status_message += "\n*Training Locked:* " + str(CFG_TRAINING_LOCKED)
    bot.sendMessage(chat_id=update.message.chat_id, text=status_message, parse_mode=telegram.ParseMode.MARKDOWN)

def t_insulted(bot, update):
    bot.sendMessage(chat_id=update.message.chat_id, text="no u")

def t_nou(bot, update):
    bot.sendMessage(chat_id=update.message.chat_id, text="no u")

def t_notcmd(bot, update):
    bot.sendMessage(chat_id=update.message.chat_id, text=update.message.from_user.first_name + " is stupid and thought this is the command line!")

# Set up handlers
def setup_handlers(s_dispatcher):
    start_handler = CommandHandler('start', c_start)
    s_dispatcher.add_handler(start_handler)

    retrain_handler = CommandHandler('retrainspeechmodel', c_manualretrain)
    s_dispatcher.add_handler(retrain_handler)

    reset_handler = CommandHandler('resetspeechmodel', c_resetmodel)
    s_dispatcher.add_handler(reset_handler)

    swords_handler = CommandHandler('liststartingwords', c_startingwords)
    s_dispatcher.add_handler(swords_handler)

    cspeechmodel_handler = CommandHandler('changespeechmodel', c_changespeechmodel)
    s_dispatcher.add_handler(cspeechmodel_handler)

    locktraining_handler = CommandHandler('locktraining', c_locktraining)
    s_dispatcher.add_handler(locktraining_handler)

    unlocktraining_handler = CommandHandler('unlocktraining', c_unlocktraining)
    s_dispatcher.add_handler(unlocktraining_handler)

    statusmessage_handler = CommandHandler('status', c_displaystatus)
    s_dispatcher.add_handler(statusmessage_handler)

    f_clear = CustomFilters.ClearFilter()
    clear_handler = MessageHandler(f_clear, t_notcmd)
    s_dispatcher.add_handler(clear_handler)

    f_nou = CustomFilters.NoUFilter()
    nou_handler = MessageHandler(f_nou, t_nou)
    s_dispatcher.add_handler(nou_handler)

    f_insult = CustomFilters.InsultingWorldFilter()
    insulted_handler = MessageHandler(f_insult, t_insulted)
    s_dispatcher.add_handler(insulted_handler)

    f_mention = CustomFilters.MentionFilter()
    markov_handler = MessageHandler(f_mention, t_markov)
    s_dispatcher.add_handler(markov_handler)

    f_private = CustomFilters.PrivateMessageFilter()
    pm_handler = MessageHandler(f_private, t_markov)
    s_dispatcher.add_handler(pm_handler)

    f_useradd = CustomFilters.UserAddedFilter()
    useradd_handler = MessageHandler(f_useradd, a_useradd)
    s_dispatcher.add_handler(useradd_handler)

    f_userleft = CustomFilters.UserLeftFilter()
    userleft_handler = MessageHandler(f_userleft, a_userleft)
    s_dispatcher.add_handler(userleft_handler)

    f_reddit = CustomFilters.RedditFilter()
    subreddit_handler = MessageHandler(f_reddit, t_reddit)
    s_dispatcher.add_handler(subreddit_handler)

    f_group = CustomFilters.InGroupFilter()
    groupmessage_handler = MessageHandler(f_group, t_train)
    s_dispatcher.add_handler(groupmessage_handler)

    echo_handler = MessageHandler(Filters.text, t_echo)
    #s_dispatcher.add_handler(echo_handler)

def read_config_file(cnf_filename):
    Config = ConfigParser.ConfigParser()
    Config.read("./" + cnf_filename)
    global CFG_TELEGRAM_API_KEY
    CFG_TELEGRAM_API_KEY = Config.get("Telegram", "APIKey")
    global CFG_SUPER_USER_ID
    CFG_SUPER_USER_ID = int(Config.get("Administration", "SuperUserID"))
    global CFG_MARKOV_CHAIN_NAME
    CFG_MARKOV_CHAIN_NAME = Config.get("Markov", "ChainName")
    global CFG_ORIGINAL_OVERLAP
    CFG_ORIGINAL_OVERLAP = float(Config.get("Markov", "OriginalOverlap"))


# Program logic
def main():
    # Set up logging
    logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    # Set config options
    read_config_file("sn0wbit.ini")

    # Get API token from config options
    API_TOKEN = CFG_TELEGRAM_API_KEY

    # Create the bot
    s_updater = Updater(token=API_TOKEN)
    s_dispatcher = s_updater.dispatcher

    # Setup handlers
    setup_handlers(s_dispatcher)

    #    Let's go!
    s_updater.start_polling()

main()
