from typing import Optional

from telegram import Update
from telegram.ext import CallbackContext

from data.local_drive import TimbreTransferAudioExample


class BaseEloQuestion(object):

    def __init__(self, eval_audio_example_1, eval_audio_example_2):
        self._my_messages: [int] = []
        self.eval_audio_example_1: TimbreTransferAudioExample = eval_audio_example_1
        self.eval_audio_example_2: TimbreTransferAudioExample = eval_audio_example_2

    def ask_user(self, update: Update, context: CallbackContext):
        pass

    def clear_messages(self, update: Update, context: CallbackContext):
        for message_id in self._my_messages:
            context.bot.delete_message(chat_id=update.effective_chat.id, message_id=message_id)

        self._my_messages.clear()

    def get_name_of_question_type(self):
        pass
