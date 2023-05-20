from copy import deepcopy
from enum import Enum

from telegram import InlineKeyboardButton, InlineKeyboardMarkup

from data.local_drive import TimbreTransferAudioExample
from data.local_drive_config import REFERENCE_AUDIO_DATASETS


class ExampleQuestionsStates(Enum):
    ShowAudioToBeEvaluated = 1
    AskAboutSourceTimbreSimilarity = 2
    AskAboutTargetTimbreSimilarity = 3
    AskAboutSoundQuality = 4
    GoNext = 5


def go_to_next_audio_example(context):
    current_audio_example: TimbreTransferAudioExample = context.user_data['selected_audio_examples'].pop(0)
    context.user_data['current_audio_example'] = current_audio_example

    return current_audio_example


def delete_n_messages_to_be_deleted(update, context, n):
    # Retrieve the message IDs from context
    message_ids = context.chat_data['message_to_be_deleted']

    # Delete the last two messages
    messages_to_remove = deepcopy(message_ids[-n:] if type(n) == int else message_ids)
    for message_id in messages_to_remove:
        context.bot.delete_message(chat_id=update.effective_chat.id, message_id=message_id)
        context.chat_data['message_to_be_deleted'].remove(message_id)


def ask_question(update, context) -> bool:
    current_audio_example: TimbreTransferAudioExample = context.user_data['current_audio_example']
    source_instrument_name: str = current_audio_example.source_instrument_name
    target_instrument_name: str = current_audio_example.target_instrument_name
    n_questions = 3 if target_instrument_name != source_instrument_name else 2

    question_number = context.user_data["questionNumber"]

    # Send the question - you'll need to replace this with your actual questions and response options
    keyboard_similarity = [
        [InlineKeyboardButton("0 🙅",    callback_data=f'{question_number}_0'),
         InlineKeyboardButton("1",      callback_data=f'{question_number}_1'),
         InlineKeyboardButton("2",      callback_data=f'{question_number}_2'),
         InlineKeyboardButton("3 🆗",    callback_data=f'{question_number}_3')],
    ]

    keyboard_audio_quality = [
        [InlineKeyboardButton("0 🤮",    callback_data=f'{question_number}_0'),
         InlineKeyboardButton("1",      callback_data=f'{question_number}_1'),
         InlineKeyboardButton("2",      callback_data=f'{question_number}_2'),
         InlineKeyboardButton("3 👍👌",   callback_data=f'{question_number}_3')],
    ]

    if context.user_data['exampleQuestionsState'] == ExampleQuestionsStates.ShowAudioToBeEvaluated:

        # Send audio to evaluate
        with open(current_audio_example.path, 'rb') as audio_file:

            message = context.bot.send_message(chat_id=update.effective_chat.id,
                                               text=f'💅🎻 Example #{context.user_data["questionNumber"]}: ({source_instrument_name} -> {target_instrument_name})')

            context.chat_data['message_to_be_deleted'] += [message.message_id]

        return True


    elif context.user_data['exampleQuestionsState'] == ExampleQuestionsStates.AskAboutSoundQuality:

        # Send audio to evaluate
        with open(current_audio_example.path, 'rb') as evaluation_audio_file:

            reply_markup = InlineKeyboardMarkup(keyboard_audio_quality)
            message = context.bot.send_audio(chat_id=update.effective_chat.id,
                                             audio=evaluation_audio_file,
                                             title='Audio to rate',
                                             caption=f'Question #1/{n_questions}: Please rate the overall sound quality and realism of the sound',
                                             reply_markup=reply_markup)

            context.chat_data['message_to_be_deleted'] += [message.message_id]

            return True


    elif context.user_data['exampleQuestionsState'] == ExampleQuestionsStates.AskAboutSourceTimbreSimilarity:

        # Send audio to evaluate
        with open(current_audio_example.path, 'rb') as evaluation_audio_file:

            reply_markup = InlineKeyboardMarkup(keyboard_similarity)
            message = context.bot.send_audio(chat_id=update.effective_chat.id,
                                             audio=evaluation_audio_file,
                                             title='Same audio to rate',
                                             caption=f'Question #2/{n_questions}: How much does it sound like a {source_instrument_name}?'
                                                     f'\n\nPlease pay attention to the sound, not individual notes',
                                             reply_markup=reply_markup)

            reference_audio_for_source_instrument = REFERENCE_AUDIO_DATASETS[0].get_by_source_instrument(source_instrument_name)[0]
            with open(reference_audio_for_source_instrument.path, 'rb') as audio_file:
                message_with_audio = context.bot.send_audio(chat_id=update.effective_chat.id,
                                                            audio=audio_file,
                                                            caption=f'This is how {source_instrument_name} actually sounds, just for reference. How much are they similar?',
                                                            title=f'{source_instrument_name}')

            context.chat_data['message_to_be_deleted'] += [message.message_id, message_with_audio.message_id]
            return True

    elif context.user_data['exampleQuestionsState'] == ExampleQuestionsStates.AskAboutTargetTimbreSimilarity:

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

                reference_audio_for_target_instrument = REFERENCE_AUDIO_DATASETS[0].get_by_target_instrument(target_instrument_name)[0]
                with open(reference_audio_for_target_instrument.path, 'rb') as audio_file:
                    message_with_audio = context.bot.send_audio(chat_id=update.effective_chat.id,
                                                                audio=audio_file,
                                                                caption=f'This is how {target_instrument_name} actually sounds.',
                                                                title=f'{target_instrument_name}')

                context.chat_data['message_to_be_deleted'] += [message.message_id, message_with_audio.message_id]

                return True

        return False


def go_to_next_question(update, context, n_examples):

    prevQuestionState = context.user_data['exampleQuestionsState']


    if prevQuestionState == ExampleQuestionsStates.GoNext:
        context.user_data['questionNumber'] += 1

        if context.user_data['questionNumber'] <= n_examples:

            go_to_next_audio_example(context=context)

            context.user_data['exampleQuestionsState'] = ExampleQuestionsStates.ShowAudioToBeEvaluated
            ask_question(update, context)

            go_to_next_question(update=update, context=context, n_examples=n_examples)

        else:

            context.bot.send_message(chat_id=update.effective_chat.id,
                                     text=f"Thanks for your participation! "
                                          f"Towards better timbre transfer neural networks, together!!!\n"
                                          f"If you want to try again, use /start command.")

    elif prevQuestionState == ExampleQuestionsStates.ShowAudioToBeEvaluated:

        context.user_data['exampleQuestionsState'] = ExampleQuestionsStates.AskAboutSoundQuality
        ask_question(update, context)

    elif prevQuestionState == ExampleQuestionsStates.AskAboutSoundQuality:

        delete_n_messages_to_be_deleted(update=update, context=context, n=1)

        context.user_data['exampleQuestionsState'] = ExampleQuestionsStates.AskAboutSourceTimbreSimilarity
        ask_question(update, context)

    elif prevQuestionState == ExampleQuestionsStates.AskAboutSourceTimbreSimilarity:

        delete_n_messages_to_be_deleted(update=update, context=context, n=2)

        context.user_data['exampleQuestionsState'] = ExampleQuestionsStates.AskAboutTargetTimbreSimilarity
        question_asked = ask_question(update, context)

        if not question_asked:
            go_to_next_question(update=update, context=context, n_examples=n_examples)


    elif prevQuestionState == ExampleQuestionsStates.AskAboutTargetTimbreSimilarity:

        delete_n_messages_to_be_deleted(update=update, context=context, n='all')

        context.user_data['exampleQuestionsState'] = ExampleQuestionsStates.GoNext
        go_to_next_question(update=update, context=context, n_examples=n_examples)

