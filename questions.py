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
    message_ids = context.chat_data.get('message_to_be_deleted', [])

    # Delete the last two messages
    for message_id in message_ids[-n:]:
        context.bot.delete_message(chat_id=update.effective_chat.id, message_id=message_id)


def ask_question(update, context) -> bool:
    current_audio_example: TimbreTransferAudioExample = context.user_data['current_audio_example']
    source_instrument_name: str = current_audio_example.source_instrument_name
    target_instrument_name: str = current_audio_example.target_instrument_name
    n_questions = 3 if target_instrument_name != source_instrument_name else 2

    # Send the question - you'll need to replace this with your actual questions and response options
    keyboard = [
        [InlineKeyboardButton("0", callback_data='1_0'),
         InlineKeyboardButton("1", callback_data='1_1'),
         InlineKeyboardButton("2", callback_data='1_2'),
         InlineKeyboardButton("3", callback_data='1_3')],
    ]

    if context.user_data['exampleQuestionsState'] == ExampleQuestionsStates.ShowAudioToBeEvaluated:

        # Send audio to evaluate
        with open(current_audio_example.path, 'rb') as audio_file:
            message = context.bot.send_audio(chat_id=update.effective_chat.id,
                                             audio=audio_file,
                                             caption=f'💅🎻 Example #{context.user_data["questionNumber"]}: Listen to the audio and answer following questions \n {str(current_audio_example)}',
                                             title=f'Audio to rate ({current_audio_example.source_instrument_name} -> {current_audio_example.target_instrument_name})')
            context.chat_data['message_with_evaluation_audio'] = message.message_id

        return True

    elif context.user_data['exampleQuestionsState'] == ExampleQuestionsStates.AskAboutSourceTimbreSimilarity:

        reply_markup = InlineKeyboardMarkup(keyboard)
        message = context.bot.send_message(chat_id=update.effective_chat.id,
                                           text=f'Question #1/{n_questions}: How much does it sound like a {current_audio_example.source_instrument_name}?\n'
                                                f'Please pay attention to the sound, not individual notes',
                                           reply_markup=reply_markup,
                                           reply_to_message_id=context.chat_data['message_with_evaluation_audio'])

        reference_audio_for_source_instrument = REFERENCE_AUDIO_DATASETS[0].get_by_source_instrument(source_instrument_name)[0]
        with open(reference_audio_for_source_instrument.path, 'rb') as audio_file:
            message_with_audio = context.bot.send_audio(chat_id=update.effective_chat.id,
                                                        audio=audio_file,
                                                        caption=f'This is how {source_instrument_name} actually sounds, just for reference. Are they similar?',
                                                        title=f'{source_instrument_name}')

        context.chat_data['message_to_be_deleted'] = [message_with_audio.message_id]
        return True

    elif context.user_data['exampleQuestionsState'] == ExampleQuestionsStates.AskAboutTargetTimbreSimilarity:

        if target_instrument_name != source_instrument_name:
            delete_n_messages_to_be_deleted(update=update, context=context, n=1)

            reply_markup = InlineKeyboardMarkup(keyboard)
            context.bot.send_message(chat_id=update.effective_chat.id,
                                     text=f'Question #2/{n_questions}: Please listen to it again.\n'
                                          f'How much does it sound like a {target_instrument_name}?\n'
                                          f'Please pay attention to the sound, not notes',
                                     reply_markup=reply_markup,
                                     reply_to_message_id=context.chat_data['message_with_evaluation_audio'])

            reference_audio_for_target_instrument = REFERENCE_AUDIO_DATASETS[0].get_by_target_instrument(target_instrument_name)[0]
            with open(reference_audio_for_target_instrument.path, 'rb') as audio_file:
                message_with_audio = context.bot.send_audio(chat_id=update.effective_chat.id,
                                                            audio=audio_file,
                                                            caption=f'This is how {target_instrument_name} actually sounds.',
                                                            title=f'{target_instrument_name}')

            context.chat_data['message_to_be_deleted'] = [message_with_audio.message_id]

            return True

        return False

    elif context.user_data['exampleQuestionsState'] == ExampleQuestionsStates.AskAboutSoundQuality:

        delete_n_messages_to_be_deleted(update=update, context=context, n=1)

        reply_markup = InlineKeyboardMarkup(keyboard)
        context.bot.send_message(chat_id=update.effective_chat.id,
                                 text=f'Question #{n_questions}/{n_questions}: Please rate the overall sound quality and realism of the sound',
                                 reply_markup=reply_markup,
                                 reply_to_message_id=context.chat_data['message_with_evaluation_audio'])

        return True


def go_to_next_question(update, context, n_examples):

    questionState = context.user_data['exampleQuestionsState']

    def go_next():
        context.user_data['questionNumber'] += 1

        if context.user_data['questionNumber'] <= n_examples:

            go_to_next_audio_example(context=context)

            context.user_data['exampleQuestionsState'] = ExampleQuestionsStates.ShowAudioToBeEvaluated
            ask_question(update, context)

            context.user_data['exampleQuestionsState'] = ExampleQuestionsStates.AskAboutSourceTimbreSimilarity
            ask_question(update, context)

        else:

            context.bot.send_message(chat_id=update.effective_chat.id,
                                     text=f"Thanks for your participation! "
                                          f"To the better timbre transfer neural networks, together!!!\n"
                                          f"If you want to try again, use /start command.")

    if questionState == ExampleQuestionsStates.GoNext:
        go_next()

    elif questionState == ExampleQuestionsStates.AskAboutSourceTimbreSimilarity:
        context.user_data['exampleQuestionsState'] = ExampleQuestionsStates.AskAboutTargetTimbreSimilarity
        ask_question(update, context)

    elif questionState == ExampleQuestionsStates.AskAboutTargetTimbreSimilarity:
        context.user_data['exampleQuestionsState'] = ExampleQuestionsStates.AskAboutSoundQuality
        question_asked = ask_question(update, context)

        if not question_asked:
            go_to_next_question(update=update, context=context, n_examples=n_examples)

    elif questionState == ExampleQuestionsStates.AskAboutSoundQuality:
        context.user_data['exampleQuestionsState'] = ExampleQuestionsStates.GoNext
        go_next()
