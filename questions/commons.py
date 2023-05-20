from copy import deepcopy

from telegram import Update
from telegram.ext import CallbackContext

from data.local_drive import TimbreTransferAudioExample


def load_next_audio_example(context: CallbackContext):
    current_audio_example: TimbreTransferAudioExample = context.user_data['selected_audio_examples'].pop(0)
    context.user_data['current_audio_example'] = current_audio_example

    return current_audio_example


def delete_n_messages_to_be_deleted(update: Update, context: CallbackContext, n):
    # Retrieve the message IDs from context
    message_ids = context.user_data['message_to_be_deleted']

    # Delete the last two messages
    messages_to_remove = deepcopy(message_ids[-n:] if type(n) == int else message_ids)
    for message_id in messages_to_remove:
        context.bot.delete_message(chat_id=update.effective_chat.id, message_id=message_id)
        context.user_data['message_to_be_deleted'].remove(message_id)
