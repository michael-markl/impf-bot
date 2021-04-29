#!/usr/bin/env python

import logging
import json
from threading import Timer
import urllib.request


from telegram import Update, ForceReply, Chat
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)

logger = logging.getLogger(__name__)

watchers = []
last_response = None

# Define a few command handlers. These usually take the two arguments update and
# context.
def start(update: Update, _: CallbackContext) -> None:
    """Send a message when the command /start is issued."""

    chat: Chat = update.effective_chat
    if chat.id not in watchers:
        watchers.append(chat.id)

        file = open("watchers.json", "w")
        file.write(json.dumps(watchers))
        file.close()

    update.message.reply_markdown_v2(
        fr"Hi\. Du bekommst jetzt alle Updates\!"
    )


def help_command(update: Update, _: CallbackContext) -> None:
    """Send a message when the command /help is issued."""
    update.message.reply_text('Help!')


def echo(update: Update, _: CallbackContext) -> None:
    """Echo the user message."""
    update.message.reply_text(update.message.text)




def notifyWatchers(updater: Updater):
    global watchers
    for watcher in watchers:
        updater.bot.send_message(chat_id=watcher, text="Das Impfdashboard wurde aktualisiert 🎉!\nhttps://impfdashboard.de")


def poll_impfdashboard(updater: Updater):
    global last_response
    try:
        contents = urllib.request.urlopen("https://impfdashboard.de/static/data/germany_vaccinations_by_state.tsv").read()
        if last_response is not None:
            if contents != last_response:
                notifyWatchers(updater)
        last_response = contents
    except Exception as e:
        logger.log(level=logging.ERROR, msg=e)
    finally:
        Timer(15, poll_impfdashboard, [updater]).start()


def main() -> None:
    """Start the bot."""
    global watchers
    # Create the Updater and pass it your bot's token.
    token = open("token.txt", "r").readline()
    watchers = json.loads(open("watchers.json", "r").read())

    updater = Updater(token)
    # Get the dispatcher to register handlers
    dispatcher = updater.dispatcher
    # on different commands - answer in Telegram
    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(CommandHandler("help", help_command))

    # on non command i.e message - echo the message on Telegram
    dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, echo))

    # Start the Bot
    updater.start_polling()
    poll_impfdashboard(updater)

    # Run the bot until you press Ctrl-C or the process receives SIGINT,
    # SIGTERM or SIGABRT. This should be used most of the time, since
    # start_polling() is non-blocking and will stop the bot gracefully.
    updater.idle()


if __name__ == '__main__':
    main()