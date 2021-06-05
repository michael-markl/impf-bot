#!/usr/bin/env python

import csv
import json
import logging
import urllib.request
from threading import Timer
from typing import Optional

from telegram import Update, Chat
from telegram.ext import Updater, CommandHandler, CallbackContext

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)

logger = logging.getLogger(__name__)

watchers = []
last_contents = None


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

def notifyWatchers(updater: Updater, first_impfidenz: Optional[float], total_impfidenz):
    global watchers
    text = "Das Impfdashboard wurde aktualisiert 🎉!\n\n"
    if first_impfidenz is not None:
        text += "Die heutige bundesweite _7-Tage-Erst-Impfidenz_ (Erstimpfungen pro Hunderttausend Einwohner und 7 Tage) beträgt:\n"
        text += f"*{first_impfidenz:.2f}*\n\n".replace('.', ',')
    if total_impfidenz is not None:
        text += "Die heutige bundesweite _7-Tage-Gesamt-Impfidenz_ (Impfungen pro Hunderttausend Einwohner und 7 Tage) beträgt:\n"
        text += f"*{total_impfidenz:.2f}*\n\n".replace('.', ',')
    text += "[https://impfdashboard.de](https://impfdashboard.de)"
    for watcher in watchers:
        try:
            updater.bot.send_message(chat_id=watcher, text=text, parse_mode='Markdown')
        except Exception as e:
            logger.log(level=logging.ERROR, msg=e)


def get_impfidenz(csv_file):
    reader = csv.reader(csv_file, delimiter="\t")
    rows = []
    for row in reader:
        rows.append(row)
    first_index = -1
    total_index = -1
    for i in range(len(rows[0])):
        if rows[0][i] == "dosen_erst_differenz_zum_vortag":
            first_index = i
            break
    for i in range(len(rows[0])):
        if rows[0][i] == "dosen_differenz_zum_vortag":
            total_index = i
            break
    erst_impfidenz = sum(int(rows[i][first_index]) for i in range(-7, 0))
    total_impfidenz = sum(int(rows[i][total_index]) for i in range(-7, 0))
    return erst_impfidenz / 831.57201, total_impfidenz / 831.57201


def poll_impfdashboard(updater: Updater):
    global last_contents
    print("Polling impfdashboard...")
    try:
        url = 'https://impfdashboard.de/static/data/germany_vaccinations_timeseries_v2.tsv'
        response = urllib.request.urlopen(url)
        lines = [l.decode('utf-8') for l in response.readlines()]
        contents = '\n'.join(lines)

        if last_contents is not None:
            if contents != last_contents:
                impfidenz = None
                try:
                    erst_impfidenz, total_impfidenz = get_impfidenz(lines)
                finally:
                    notifyWatchers(updater, erst_impfidenz, total_impfidenz)
        last_contents = contents
    except Exception as e:
        logger.log(level=logging.ERROR, msg=e)
    finally:
        Timer(15, poll_impfdashboard, [updater]).start()


def main() -> None:
    """Start the bot."""
    global watchers
    token = open("token.txt", "r").readline()
    watchers = json.loads(open("watchers.json", "r").read())

    updater = Updater(token)
    dispatcher = updater.dispatcher
    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(CommandHandler("help", help_command))

    updater.start_polling()
    poll_impfdashboard(updater)

    updater.idle()


if __name__ == '__main__':
    main()
