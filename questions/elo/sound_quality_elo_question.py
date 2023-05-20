from telegram import InlineKeyboardButton, Update, InlineKeyboardMarkup
from telegram.ext import CallbackContext

from data.local_drive import AudioDatasetPerFolderCollection, TimbreTransferAudioExample
from questions.elo.base_elo_question import BaseEloQuestion


class SoundQualityEloQuestion(BaseEloQuestion):

    def __init__(self, eval_datasets: AudioDatasetPerFolderCollection):
        eval_audio_example_1 = eval_datasets.pick_random_audio_example()
        self.source_instrument = eval_audio_example_1.source_instrument_name

        super().__init__(eval_audio_example_1=eval_audio_example_1,
                         eval_audio_example_2=eval_datasets.pick_random_audio_example_by_source_instrument(
                             source_instrument=self.source_instrument))

        self.keyboard = [
            [InlineKeyboardButton("Audio #1", callback_data=f'ELO_1_0_2_1'),  # ELO_Example_Score
             InlineKeyboardButton("Audio #2", callback_data=f'ELO_1_1_2_0')],
        ]

    def ask_user(self, update: Update, context: CallbackContext):
        # Send audio #1 for evaluation

        with open(self.eval_audio_example_1.path, 'rb') as evaluation_audio_file:
            message_audio_1 = context.bot.send_audio(chat_id=update.effective_chat.id,
                                                     audio=evaluation_audio_file,
                                                     title='Audio #1',
                                                     caption=f'Audio #1')

            self._my_messages += [message_audio_1.message_id]

        # Send audio #2 for evaluation

        with open(self.eval_audio_example_2.path, 'rb') as evaluation_audio_file:
            message_audio_2 = context.bot.send_audio(chat_id=update.effective_chat.id,
                                                     audio=evaluation_audio_file,
                                                     title='Audio #2',
                                                     caption=f'Audio #2')

            self._my_messages += [message_audio_2.message_id]

        with open(self.eval_audio_example_2.path, 'rb') as evaluation_audio_file:
            reply_markup = InlineKeyboardMarkup(self.keyboard)
            message_question = context.bot.send_message(chat_id=update.effective_chat.id,
                                                        text=f'Which audio sounds less realistic and has worse quality?',
                                                        reply_markup=reply_markup)

            self._my_messages += [message_question.message_id]

    def get_name_of_question_type(self):
        return 'sound_quality'
