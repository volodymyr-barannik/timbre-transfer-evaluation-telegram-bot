# Importing additional required modules
import os
import pickle

import gspread
from google.auth.transport.requests import Request
from google.oauth2.service_account import Credentials


CREDENTIALS_FILE = None


# Function to load the credentials and open the Google Sheets document
def get_worksheet():
    creds = None
    # The file token.pickle stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first time.
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            creds = Credentials.from_authorized_user_file(CREDENTIALS_FILE,
                                                          ['https://www.googleapis.com/auth/spreadsheets'])
            # Save the credentials for the next run
            with open('token.pickle', 'wb') as token:
                pickle.dump(creds, token)

    gc = gspread.authorize(creds)

    # Replace 'TestSheet' with the name of your Google Sheets document
    sh = gc.open('TestSheet')

    # Assuming you're working with the first worksheet in the document
    worksheet = sh.sheet1
    return worksheet


#my_worksheet = get_worksheet()
my_worksheet = None

# Function to write a user's response to Google Sheets
def record_response(worksheet, chat_id: str, question_number: str, response: str):
    # Append the response to the worksheet
    # You may want to customize this depending on how you want to structure your data
    worksheet.append_row([chat_id, question_number, response])

