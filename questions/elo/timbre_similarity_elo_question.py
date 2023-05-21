from enum import Enum
from typing import Optional

from telegram import InlineKeyboardButton, Update, InlineKeyboardMarkup
from telegram.ext import CallbackContext

from data.local_drive import AudioDatasetPerFolderCollection, TimbreTransferAudioExample, AudioExampleInstrumentType
from questions.elo.base_elo_question import BaseEloQuestion


# Measures timbre similarity to target or source instrument
class TimbreSimilarityEloQuestion(BaseEloQuestion):

    def __init__(self,
                 eval_datasets: AudioDatasetPerFolderCollection,
                 reference_datasets: AudioDatasetPerFolderCollection,
                 instrument_type: AudioExampleInstrumentType):
        eval_audio_example_1: TimbreTransferAudioExample = eval_datasets.pick_random_audio_example()

        self._instrument_type = instrument_type


        self._comparison_instrument: str = eval_audio_example_1.get_instrument_by_type(instrument_type=self._instrument_type)

        def has_good_instrument_and_is_from_other_dataset(ex: TimbreTransferAudioExample):
            ex_instr = ex.get_instrument_by_type(instrument_type=self._instrument_type)
            return ex_instr == self._comparison_instrument and not ex.src_folder.is_same_as(eval_audio_example_1.src_folder)

        # Extract second audio with same _instrument_type instrument
        eval_audio_example_2: TimbreTransferAudioExample = eval_datasets.pick_random_audio_example_by_predicate(
            predicate=has_good_instrument_and_is_from_other_dataset)

        super().__init__(eval_audio_example_1=eval_audio_example_1,
                         eval_audio_example_2=eval_audio_example_2)

        self._reference_audio_example = reference_datasets.pick_random_audio_example_by_predicate(
            predicate=lambda ex: ex.get_instrument_by_type(instrument_type=self._instrument_type) == self._comparison_instrument)

        self.keyboard = [
            [
                InlineKeyboardButton("Nobody", callback_data=f'ELO_1_0_2_0'),  # ELO_Example_Score
                InlineKeyboardButton("Audio #1", callback_data=f'ELO_1_1_2_0' if self.eval_audio_example_1.target_instrument_name == self._comparison_instrument else f'ELO_1_0_2_1'),  # _instrument_type defines whether it's a positive or negative question
                InlineKeyboardButton("Audio #2", callback_data=f'ELO_1_0_2_1' if self.eval_audio_example_2.target_instrument_name == self._comparison_instrument else f'ELO_1_1_2_0'),
                InlineKeyboardButton("Both same", callback_data=f'ELO_1_1_2_1'),

            ]
        ]

    def ask_user(self, update: Update, context: CallbackContext, debug=True):
        # Send audio #1 for evaluation

        with open(self.eval_audio_example_1.path, 'rb') as evaluation_audio_file:
            message_audio_1 = context.bot.send_audio(chat_id=update.effective_chat.id,
                                                     audio=evaluation_audio_file,
                                                     title='Audio #1',
                                                     caption=f'Audio #1\n{str(self.eval_audio_example_1) if debug is True else ""}')

            self._my_messages += [message_audio_1.message_id]

        # Send audio #2 for evaluation

        with open(self.eval_audio_example_2.path, 'rb') as evaluation_audio_file:
            message_audio_2 = context.bot.send_audio(chat_id=update.effective_chat.id,
                                                     audio=evaluation_audio_file,
                                                     title='Audio #2',
                                                     caption=f'Audio #2\n{str(self.eval_audio_example_2) if debug is True else ""}')

            self._my_messages += [message_audio_2.message_id]

        reply_markup = InlineKeyboardMarkup(self.keyboard)
        message_question = context.bot.send_message(chat_id=update.effective_chat.id,
                                                    text=f'Which audio sounds more like a {self._comparison_instrument}?',
                                                    reply_markup=reply_markup)

        self._my_messages += [message_question.message_id]

        with open(self._reference_audio_example.path, 'rb') as reference_audio_file:
            message_reference_audio = context.bot.send_audio(chat_id=update.effective_chat.id,
                                                             audio=reference_audio_file,
                                                             title=f'{self._comparison_instrument.capitalize()}',
                                                             caption=f'Just for reference, here\'s how {self._comparison_instrument} sounds in real life')

            self._my_messages += [message_reference_audio.message_id]

    def get_name_of_question_type(self):
        return f'timbre_similarity_{"target" if self._instrument_type == AudioExampleInstrumentType.TargetInstrument else "source"}'