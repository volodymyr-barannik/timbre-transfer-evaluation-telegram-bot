import logging
import platform
import sys
import time
import uuid
from enum import Enum
from typing import Optional
import telegram
from secret import TOKEN, PUSH_BOT_TOKEN, MY_CHAT_ID


class TelegramBotHandler(logging.Handler):
    def __init__(self, token, chat_id):
        logging.Handler.__init__(self)
        self.chat_id = chat_id
        self.bot = telegram.Bot(token=token)

    def emit(self, record):
        log_entry = self.format(record)
        self.bot.send_message(chat_id=self.chat_id, text=log_entry)


log_file = f"logs/logs.log"
print(f'Logging to {log_file}')

sys.stdout.reconfigure(encoding='utf-8')

telegram_handler = TelegramBotHandler(token=PUSH_BOT_TOKEN, chat_id=MY_CHAT_ID)
telegram_handler.setLevel(logging.INFO)

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s: %(message)s',
                    handlers=[
                        logging.FileHandler(log_file, encoding='utf-8'),
                        logging.StreamHandler(sys.stdout),
                        telegram_handler
                    ])


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


# It should always be on top!
apply_module_path(original_ddsp_module_path)
apply_module_path(original_midi_ddsp_module_path)

import itertools

from data.postgresql.elo.postgresql_operations import get_n_elo_records
from data.local_drive_config import EVAL_AUDIO_DATASETS, EVAL_AUDIO_DATASETS_COLLECTION, \
    REFERENCE_AUDIO_DATASETS_COLLECTION
from questions.absolute_scores.absolute_score_questions import go_to_next_question
from data.local_drive import TimbreTransferAudioExample
from data.postgresql import postgresql_operations
from questions.states import ExampleQuestionsStates

from questions.commons import delete_n_messages_to_be_deleted
from questions.elo.elo_questions import RandomEloQuestionsStateMachine
from questions.elo.sound_quality_elo_question import SoundQualityEloQuestion
from questions.elo.timbre_similarity_elo_question import BaseTimbreSimilarityEloQuestion, \
    SourceTimbreSimilarityEloQuestion, TargetTimbreSimilarityEloQuestion

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import Updater, CommandHandler, CallbackContext, CallbackQueryHandler
import random


# from oauth2client.service_account import ServiceAccountCredentials


class PollMode(Enum):
    AbsoluteScores = 1
    ELO = 2


N_EXAMPLES = 5  # Replace with your desired number of questions
M_REPRESENTATIVES_FROM_EACH_DATASET = 2  # Replace with your desired number of samples per folder
MODE: PollMode = PollMode.ELO


# Define command handler for the /start command
def start(update: Update, context: CallbackContext) -> None:
    if MODE == PollMode.AbsoluteScores:

        context.user_data['message_to_be_deleted'] = []

        keyboard = [
            [InlineKeyboardButton("Go!", callback_data='go')],
        ]

        reply_markup = InlineKeyboardMarkup(keyboard)
        message = update.message.reply_text(f'Hello. I\'ll ask you {N_EXAMPLES} questions.\n'
                                            f'Each question has a 4-second audio that was generated by a neural network. You need to give it a mark.'
                                            f'\n\nIf something sounds really bad 🤮 then give the lowest mark'
                                            f'\nIf something sounds good to you 🥰 then give a max mark, don\'t be shy'
                                            f'\n\nYour marks will make the neural networks better. Ready?',
                                            reply_markup=reply_markup)

        context.user_data['message_to_be_deleted'] += [message.message_id]

    elif MODE == PollMode.ELO:

        state_machine = RandomEloQuestionsStateMachine(
            n_examples_to_show=N_EXAMPLES,
            question_types_and_probabilities={SoundQualityEloQuestion: 0.3,
                                              SourceTimbreSimilarityEloQuestion: 0.3,
                                              TargetTimbreSimilarityEloQuestion: 0.4},
            eval_datasets=EVAL_AUDIO_DATASETS_COLLECTION,
            reference_datasets=REFERENCE_AUDIO_DATASETS_COLLECTION)

        context.user_data['state_machine'] = state_machine
        state_machine.suggest_to_start(update=update, context=context)


def say_that_we_need_to_restart_the_bot(update: Update, context: CallbackContext):
    context.bot.send_message(chat_id=update.effective_chat.id,
                             text=f'Hey, we\'ve made some improvements to the bot, so you need to /restart it.')


def statistics(update: Update, context: CallbackContext) -> None:

    n_responses: int = get_n_elo_records()
    context.bot.send_message(chat_id=update.effective_chat.id,
                             text=f'{n_responses} responses collected.')


# Define callback handler for the Go button
def poll_response(update: Update, context: CallbackContext) -> None:
    query = update.callback_query

    if MODE == PollMode.AbsoluteScores:

        if '_' in query.data:
            question_number, mark = query.data.split('_')
            question_shown_timestamp = context.user_data['question_shown_timestamp']
            question_answered_timestamp = time.time()
            time_to_answer_the_previous_question = question_answered_timestamp - question_shown_timestamp

            current_audio_example: TimbreTransferAudioExample = context.user_data['current_audio_example']

            postgresql_operations.record_answer(conn=postgresql_operations.conn,
                                                poll_uuid=context.user_data['poll_uuid'],
                                                example_audio=current_audio_example,
                                                example_number=context.user_data['example_number'],
                                                question_type=context.user_data['example_questions_state'],
                                                mark=mark,
                                                time_to_rate_example=time_to_answer_the_previous_question)

            go_to_next_question(update=update, context=context, n_examples=N_EXAMPLES)

        if query.data == 'go':
            poll_uuid = str(uuid.uuid4())
            context.user_data['poll_uuid'] = poll_uuid

            # remove introductory message
            delete_n_messages_to_be_deleted(update=update, context=context, n=1)

            # Randomly select N audio files from the complete list
            selected_audio_examples = [ds.get_random_batch(M_REPRESENTATIVES_FROM_EACH_DATASET) for ds in
                                       EVAL_AUDIO_DATASETS]
            selected_audio_examples: [TimbreTransferAudioExample] = list(
                itertools.chain(*selected_audio_examples))  # Flatten
            random.shuffle(selected_audio_examples)
            context.user_data['selected_audio_examples'] = selected_audio_examples

            context.user_data['example_number'] = 0
            context.user_data['example_questions_state'] = ExampleQuestionsStates.GoNext

            go_to_next_question(update=update, context=context, n_examples=N_EXAMPLES)

    elif MODE == PollMode.ELO:

        state_machine: Optional[RandomEloQuestionsStateMachine] = None
        if 'state_machine' in context.user_data:
            state_machine: RandomEloQuestionsStateMachine = context.user_data['state_machine']
        else:
            say_that_we_need_to_restart_the_bot(update=update, context=context)
            return

        state_machine.process_reply(update=update, context=context)
        state_machine.ask_next_question(update=update, context=context)


def restart(update: Update, context: CallbackContext) -> None:
    context.bot.send_message(chat_id=update.effective_chat.id,
                             text='The poll has been restarted. You can start again by typing /start.')


def main() -> None:
    updater = Updater(TOKEN)

    updater.dispatcher.add_handler(CommandHandler('start', start))
    updater.dispatcher.add_handler(CallbackQueryHandler(poll_response))

    updater.dispatcher.add_handler(CommandHandler('restart', start))
    updater.dispatcher.add_handler(CommandHandler('statistics', statistics))

    updater.start_polling()

    updater.idle()


if __name__ == '__main__':
    main()
