import gspread
from google.oauth2.service_account import Credentials
from gspread import Worksheet

from data.local_drive import TimbreTransferAudioExample
from data.spreadsheets.spreadsheets import GSP_SERVICE_ACCOUNT_FILE, GSP_SPREADSHEET_NAME


# Function to load the credentials and open the Google Sheets document
from questions.questions import ExampleQuestionsStates


def get_worksheet():
    # Use creds to create a client to interact with the Google Drive API
    scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
    creds = Credentials.from_service_account_file(GSP_SERVICE_ACCOUNT_FILE, scopes=scope)
    client = gspread.authorize(creds)

    worksheet = client.open(GSP_SPREADSHEET_NAME).get_worksheet(index=0)

    return worksheet


my_worksheet = get_worksheet()


# Function to write a metadata for the example and model being evaluated to Google Sheets
def record_example_metadata(worksheet: Worksheet,
                            poll_uuid: str,
                            chat_id: str,
                            username: str,
                            user_first_name: str,
                            example_number: int,
                            example_audio: TimbreTransferAudioExample):

    worksheet.append_row([poll_uuid,                                    # poll uuid
                          chat_id,                                      # chat id
                          username,                                     # username
                          user_first_name,                              # user first name
                          example_number,                               # example number
                          example_audio.src_folder.title,               # model title
                          example_audio.src_folder.folder_path,         # folder path
                          example_audio.src_folder.training_dataset,    # folder path
                          example_audio.source_instrument_name,         # source instrument
                          example_audio.target_instrument_name]         # target instrument
)


def record_answer(worksheet: Worksheet,
                  poll_uuid: str,
                  example_audio: TimbreTransferAudioExample,
                  example_number: str,
                  question_type: ExampleQuestionsStates,
                  mark: str,
                  time_to_rate_example: int):

    example_number = str(example_number)

    cells_with_our_uuid = worksheet.findall(poll_uuid, in_column=1)
    our_cell = None
    for cell in cells_with_our_uuid:
        found_example_number = worksheet.cell(row=cell.row, col=5).value

        if found_example_number == example_number:
            our_cell = cell

    assert (our_cell is not None)

    row_idx = our_cell.row

    source_instrument_name: str = example_audio.source_instrument_name
    target_instrument_name: str = example_audio.target_instrument_name

    if question_type == ExampleQuestionsStates.AskAboutSoundQuality:
        worksheet.update_cell(value=mark, row=row_idx, col=11)
        worksheet.update_cell(value=time_to_rate_example, row=row_idx, col=12)

    elif question_type == ExampleQuestionsStates.AskAboutSourceTimbreSimilarity:
        worksheet.update_cell(value=mark, row=row_idx, col=13)
        worksheet.update_cell(value=time_to_rate_example, row=row_idx, col=14)

        if source_instrument_name == target_instrument_name:
            record_answer(worksheet=worksheet,
                          poll_uuid=poll_uuid,
                          example_audio=example_audio,
                          example_number=example_number,
                          question_type=ExampleQuestionsStates.AskAboutTargetTimbreSimilarity,
                          mark=mark,
                          time_to_rate_example=time_to_rate_example)

    elif question_type == ExampleQuestionsStates.AskAboutTargetTimbreSimilarity:
        worksheet.update_cell(value=mark, row=row_idx, col=15)
        worksheet.update_cell(value=time_to_rate_example, row=row_idx, col=16)

