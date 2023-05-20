import time
from copy import deepcopy
from enum import Enum

from telegram import InlineKeyboardButton, InlineKeyboardMarkup

from data.postgresql import postgresql_operations
from data.local_drive import TimbreTransferAudioExample
from data.local_drive_config import REFERENCE_AUDIO_DATASETS
from data.sqlite import sqlite
from questions.commons import load_next_audio_example, delete_n_messages_to_be_deleted
from questions.states import ExampleQuestionsStates


def ask_question(update, context, max_number_of_examples) -> bool:
    current_audio_example: TimbreTransferAudioExample = context.user_data['current_audio_example']
    source_instrument_name: str = current_audio_example.source_instrument_name
    target_instrument_name: str = current_audio_example.target_instrument_name
    n_questions = 3 if target_instrument_name != source_instrument_name else 2

    question_type: ExampleQuestionsStates = context.user_data['example_questions_state']
    example_number = context.user_data["example_number"]
    question_number = context.user_data["question_number"]

    # Send the question - you'll need to replace this with your actual questions and response options
    keyboard_similarity = [
        [InlineKeyboardButton("0 🙅", callback_data=f'{question_number}_0'),
         InlineKeyboardButton("1", callback_data=f'{question_number}_1'),
         InlineKeyboardButton("2", callback_data=f'{question_number}_2'),
         InlineKeyboardButton("3 🆗", callback_data=f'{question_number}_3')],
    ]

    keyboard_audio_quality = [
        [InlineKeyboardButton("0 🤮", callback_data=f'{question_number}_0'),
         InlineKeyboardButton("1", callback_data=f'{question_number}_1'),
         InlineKeyboardButton("2", callback_data=f'{question_number}_2'),
         InlineKeyboardButton("3 👍👌", callback_data=f'{question_number}_3')],
    ]

    if question_type == ExampleQuestionsStates.ShowExampleNumber:

        message = context.bot.send_message(chat_id=update.effective_chat.id,
                                           text=f'💅🎻 Example #{example_number}/{max_number_of_examples}: '
                                                f'({source_instrument_name} -> {target_instrument_name})'
                                                f'\n\n {str(current_audio_example)}')

        context.user_data['message_to_be_deleted'] += [message.message_id]

        return True


    elif question_type == ExampleQuestionsStates.AskAboutSoundQuality:

        # Send audio to evaluate
        with open(current_audio_example.path, 'rb') as evaluation_audio_file:

            reply_markup = InlineKeyboardMarkup(keyboard_audio_quality)
            message = context.bot.send_audio(chat_id=update.effective_chat.id,
                                             audio=evaluation_audio_file,
                                             title='Audio to rate',
                                             caption=f'Question #1/{n_questions}: Please rate the overall sound quality and realism of the sound',
                                             reply_markup=reply_markup)

            context.user_data['message_to_be_deleted'] += [message.message_id]

            return True


    elif question_type == ExampleQuestionsStates.AskAboutSourceTimbreSimilarity:

        # Send audio to evaluate
        with open(current_audio_example.path, 'rb') as evaluation_audio_file:

            reply_markup = InlineKeyboardMarkup(keyboard_similarity)
            message = context.bot.send_audio(chat_id=update.effective_chat.id,
                                             audio=evaluation_audio_file,
                                             title='Same audio to rate',
                                             caption=f'Question #2/{n_questions}: How much does it sound like a {source_instrument_name}?'
                                                     f'\n\nPlease pay attention to the sound, not individual notes',
                                             reply_markup=reply_markup)

            reference_audio_for_source_instrument = \
            REFERENCE_AUDIO_DATASETS[0].get_by_source_instrument(source_instrument_name)[0]
            with open(reference_audio_for_source_instrument.path, 'rb') as audio_file:
                message_with_audio = context.bot.send_audio(chat_id=update.effective_chat.id,
                                                            audio=audio_file,
                                                            caption=f'Just for reference, this is how {source_instrument_name} actually sounds. How much are they similar?',
                                                            title=f'{source_instrument_name}')

            context.user_data['message_to_be_deleted'] += [message.message_id, message_with_audio.message_id]

            return True

    elif question_type == ExampleQuestionsStates.AskAboutTargetTimbreSimilarity:

        if target_instrument_name != source_instrument_name:
            # Send audio to evaluate
            with open(current_audio_example.path, 'rb') as evaluation_audio_file:
                reply_markup = InlineKeyboardMarkup(keyboard_similarity)
                message = context.bot.send_audio(chat_id=update.effective_chat.id,
                                                 audio=evaluation_audio_file,
                                                 title='Same audio to to rate',
                                                 caption=f'Question #{n_questions}/{n_questions}: How much does it sound like a {target_instrument_name}?'
                                                         f'\n\nPlease pay attention to the sound, not individual notes',
                                                 reply_markup=reply_markup)

                reference_audio_for_target_instrument = \
                REFERENCE_AUDIO_DATASETS[0].get_by_target_instrument(target_instrument_name)[0]
                with open(reference_audio_for_target_instrument.path, 'rb') as audio_file:
                    message_with_audio = context.bot.send_audio(chat_id=update.effective_chat.id,
                                                                audio=audio_file,
                                                                caption=f'This is how {target_instrument_name} actually sounds.',
                                                                title=f'{target_instrument_name}')

                context.user_data['message_to_be_deleted'] += [message.message_id, message_with_audio.message_id]

                return True

        return False


def go_to_next_question(update, context, n_examples):
    prevQuestionState = context.user_data['example_questions_state']

    if prevQuestionState == ExampleQuestionsStates.GoNext:
        context.user_data['example_number'] += 1

        if context.user_data['example_number'] <= n_examples:

            load_next_audio_example(context=context)

            user = update.effective_chat

            postgresql_operations.record_example_metadata(conn=postgresql_operations.conn,
                                                          poll_uuid=context.user_data['poll_uuid'],
                                                          chat_id=update.effective_chat.id,
                                                          username=user.username,
                                                          user_first_name=user.first_name,
                                                          example_number=context.user_data['example_number'],
                                                          example_audio=context.user_data['current_audio_example'])

            context.user_data['example_questions_state'] = ExampleQuestionsStates.ShowExampleNumber
            context.user_data['question_number'] = 0
            ask_question(update, context, max_number_of_examples=n_examples)

            go_to_next_question(update=update, context=context, n_examples=n_examples)

        else:

            context.bot.send_message(chat_id=update.effective_chat.id,
                                     text=f"Thanks for your participation! "
                                          f"Towards better timbre transfer neural networks, together!!!\n"
                                          f"If you want to try again, use /start command.")

    elif prevQuestionState == ExampleQuestionsStates.ShowExampleNumber:

        context.user_data['example_questions_state'] = ExampleQuestionsStates.AskAboutSoundQuality
        context.user_data['question_number'] = 1

        ask_question(update, context, max_number_of_examples=n_examples)
        context.user_data['question_shown_timestamp'] = time.time()


    elif prevQuestionState == ExampleQuestionsStates.AskAboutSoundQuality:

        delete_n_messages_to_be_deleted(update=update, context=context, n=1)

        context.user_data['example_questions_state'] = ExampleQuestionsStates.AskAboutSourceTimbreSimilarity
        context.user_data['question_number'] = 2

        ask_question(update, context, max_number_of_examples=n_examples)
        context.user_data['question_shown_timestamp'] = time.time()


    elif prevQuestionState == ExampleQuestionsStates.AskAboutSourceTimbreSimilarity:

        delete_n_messages_to_be_deleted(update=update, context=context, n=2)

        context.user_data['example_questions_state'] = ExampleQuestionsStates.AskAboutTargetTimbreSimilarity
        context.user_data['question_number'] = 3

        question_asked = ask_question(update, context, max_number_of_examples=n_examples)
        context.user_data['question_shown_timestamp'] = time.time()

        if not question_asked:
            go_to_next_question(update=update, context=context, n_examples=n_examples)


    elif prevQuestionState == ExampleQuestionsStates.AskAboutTargetTimbreSimilarity:

        delete_n_messages_to_be_deleted(update=update, context=context, n='all')

        context.user_data['example_questions_state'] = ExampleQuestionsStates.GoNext
        go_to_next_question(update=update, context=context, n_examples=n_examples)
