import sqlite3
import threading
from sqlite3 import Connection

from data.local_drive import TimbreTransferAudioExample

DB_NAME = 'survey_data.db'

local_storage = threading.local()


def get_sqlite_conn():
    # Get the current SQLite connection or create a new one
    db = getattr(local_storage, 'db', None)
    if db is None:
        db = local_storage.db = sqlite3.connect(DB_NAME)
    return db


def init_table(conn):
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE survey_results(
            poll_uuid TEXT,
            chat_id TEXT,
            username TEXT,
            user_first_name TEXT,
            
            
            example_number INTEGER,
            
            model_title TEXT,
            path TEXT,
            training_dataset TEXT,
            source_instrument TEXT,
            target_instrument TEXT,
        
            
            sound_quality INTEGER,
            sound_quality_time_taken DOUBLE,
            
            source_timbre_similarity INTEGER,
            source_timbre_similarity_time_taken DOUBLE,
            
            target_timbre_similarity INTEGER,
            target_timbre_similarity_time_taken DOUBLE);
    ''')
    conn.commit()  # Saves the changes


def record_example_metadata(conn: Connection,
                            poll_uuid: str,
                            chat_id: str,
                            username: str,
                            user_first_name: str,
                            example_number: int,
                            example_audio: TimbreTransferAudioExample):

    cursor = conn.cursor()

    data = [poll_uuid,                                      # poll uuid
           chat_id,                                         # chat id
           username,                                        # username
           user_first_name,                                 # user first name
           example_number,                                  # example number
           example_audio.src_folder.title,                  # model title
           example_audio.src_folder.folder_path,            # folder path
           example_audio.src_folder.training_dataset,       # folder path
           example_audio.source_instrument_name,            # source instrument
           example_audio.target_instrument_name]            # target instrument

    cursor.execute('''
        INSERT INTO survey_results(
                    poll_uuid, 
                    chat_id, 
                    username, 
                    user_first_name, 
                    example_number, 
                    model_title, 
                    path, 
                    training_dataset, 
                    source_instrument, 
                    target_instrument)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', data)

    # Save (commit) the changes and close connection
    conn.commit()
