import platform
import sys
from enum import Enum

from secret import TOKEN

if platform.system() == 'Windows':
    original_midi_ddsp_module_path = 'E:/Code/Projects/TimbreTransfer/original-midi-ddsp/'
    original_ddsp_module_path = 'E:/Code/Projects/TimbreTransfer/original-ddsp-for-vst-debugging/'


def apply_module_path(module_path):
    print(f"module_path={module_path}")
    if module_path not in sys.path:
      sys.path.append(module_path)
      print(f"appending {module_path} to sys.path")
    else:
      print(f"do not appending {module_path} to sys.path")

apply_module_path(original_ddsp_module_path)
apply_module_path(original_midi_ddsp_module_path)

import itertools

from data import spreadsheets
from data.local_drive_config import EVAL_AUDIO_DATASETS, REFERENCE_AUDIO_DATASETS
from questions import ask_question, ExampleQuestionsStates, go_to_next_audio_example, go_to_next_question
from data.local_drive import TimbreTransferAudioExample

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import Updater, CommandHandler, CallbackContext, CallbackQueryHandler
import random

#from oauth2client.service_account import ServiceAccountCredentials


N = 14  # Replace with your desired number of questions
M = 2  # Replace with your desired number of samples per folder


# Define command handler for the /start command
def start(update: Update, context: CallbackContext) -> None:
    keyboard = [
        [InlineKeyboardButton("Go!", callback_data='go')],
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)
    update.message.reply_text(f'Hello. I\'ll ask you {N} questions. Ready?', reply_markup=reply_markup)


# Define callback handler for the Go button
def button(update: Update, context: CallbackContext) -> None:
    query = update.callback_query

    if '_' in query.data:
        # This is one of the answer buttons
        question_number, answer = query.data.split('_')

        # Store this question's answer in user_data
        context.user_data[question_number] = answer

        # Record the response in Google Sheets
        #spreadsheets.record_response(spreadsheets.my_worksheet, update.effective_chat.id, question_number, answer)

        go_to_next_question(update=update, context=context, n_examples=N)

    if query.data == 'go':
        # Send the first audio file and question

        context.user_data['questionNumber'] = 1
        context.user_data['exampleQuestionsState'] = ExampleQuestionsStates.GoNext

        context.user_data['exampleQuestionsState'] = ExampleQuestionsStates.ShowAudioToBeEvaluated

        # Randomly select N audio files from the complete list
        selected_audio_examples = [ds.get_random_batch(M) for ds in EVAL_AUDIO_DATASETS]
        selected_audio_examples: [TimbreTransferAudioExample] = list(itertools.chain(*selected_audio_examples))  # Flatten
        random.shuffle(selected_audio_examples)
        context.user_data['selected_audio_examples'] = selected_audio_examples

        current_audio_example: TimbreTransferAudioExample = go_to_next_audio_example(context=context)

        # Show references
        context.user_data['exampleQuestionsState'] = ExampleQuestionsStates.ShowAudioToBeEvaluated
        ask_question(update, context)

        # And now ask questions!

        context.user_data['exampleQuestionsState'] = ExampleQuestionsStates.AskAboutSourceTimbreSimilarity
        ask_question(update, context)


def restart(update: Update, context: CallbackContext) -> None:

    context.bot.send_message(chat_id=update.effective_chat.id,
                             text='The poll has been restarted. You can start again by typing /start.')

def main() -> None:
    updater = Updater(TOKEN)

    updater.dispatcher.add_handler(CommandHandler('start', start))
    updater.dispatcher.add_handler(CallbackQueryHandler(button))

    updater.dispatcher.add_handler(CommandHandler('restart', restart))

    updater.start_polling()

    updater.idle()


if __name__ == '__main__':
    main()