import os
import pickle

import gspread
from google.auth.transport.requests import Request
from google.oauth2.service_account import Credentials

from data.spreadsheets_secrets.spreadsheets_secret import GSP_SERVICE_ACCOUNT_FILE, GSP_SPREADSHEET_NAME


# Function to load the credentials and open the Google Sheets document
def get_worksheet():
    # Use creds to create a client to interact with the Google Drive API
    scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
    creds = Credentials.from_service_account_file(GSP_SERVICE_ACCOUNT_FILE, scopes=scope)
    client = gspread.authorize(creds)

    worksheet = client.open(GSP_SPREADSHEET_NAME).sheet1

    return worksheet


my_worksheet = get_worksheet()
#my_worksheet = None

# Function to write a user's response to Google Sheets
def record_response(worksheet, chat_id: str, question_number: str, response: str):
    # Append the response to the worksheet
    # You may want to customize this depending on how you want to structure your data
    worksheet.append_row([chat_id, question_number, response])
