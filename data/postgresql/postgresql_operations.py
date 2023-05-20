import psycopg2

from data.local_drive import TimbreTransferAudioExample
from data.postgresql.secrets import PG_DB_NAME, PG_DB_USERNAME, PG_DB_PASSWORD
from questions.states import ExampleQuestionsStates

conn = psycopg2.connect(
    dbname=PG_DB_NAME,
    user=PG_DB_USERNAME,
    password=PG_DB_PASSWORD,
    host="localhost",
    port="5432"
)

print(conn)

cur = conn.cursor()


cur = conn.cursor()

# Execute the command
cur.execute("SELECT current_database();")

# Fetch and print the result
current_db = cur.fetchone()[0]
print(f"Connected to database: {current_db}")

# Close the cursor and the connection
cur.close()


# Create a new cursor object
cur = conn.cursor()

# Execute the command
cur.execute("SELECT current_user;")

# Fetch and print the result
current_user = cur.fetchone()[0]
print(f"Connected as user: {current_user}")

# Close the cursor and the connection
cur.close()


def init_table():
    # Create a new cursor object
    cur = conn.cursor()

    # Execute the CREATE TABLE command
    cur.execute('''
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
            sound_quality_time_taken REAL,
            
            source_timbre_similarity INTEGER,
            source_timbre_similarity_time_taken REAL,
            
            target_timbre_similarity INTEGER,
            target_timbre_similarity_time_taken REAL);
    ''')

    # Commit the transaction
    conn.commit()

    # Close the cursor and the connection
    cur.close()


def record_example_metadata(conn,
                            poll_uuid: str,
                            chat_id: str,
                            username: str,
                            user_first_name: str,
                            example_number: int,
                            example_audio: TimbreTransferAudioExample):

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

    # Create a new cursor object
    cur = conn.cursor()

    # Prepare the INSERT INTO command
    insert_cmd = '''
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
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s);
    '''

    # Execute the INSERT INTO command
    cur.execute(insert_cmd, data)

    # Commit the transaction
    conn.commit()

    # Close the cursor and the connection
    cur.close()


def record_answer(conn: psycopg2.extensions.connection,
                  poll_uuid: str,
                  example_audio: TimbreTransferAudioExample,
                  example_number: str,
                  question_type: ExampleQuestionsStates,
                  mark: str,
                  time_to_rate_example: int):
    example_number = str(example_number)

    cur = conn.cursor()

    cur.execute(
        "SELECT * "
        "FROM survey_results "
        "WHERE poll_uuid = %s AND example_number = %s;",
        (poll_uuid, example_number,)
    )

    row = cur.fetchone()
    assert row is not None, 'Row not found in the database'

    source_instrument_name: str = example_audio.source_instrument_name
    target_instrument_name: str = example_audio.target_instrument_name

    if question_type == ExampleQuestionsStates.AskAboutSoundQuality:
        cur.execute(
            ''' UPDATE survey_results 
                SET sound_quality = %s, sound_quality_time_taken = %s 
                WHERE poll_uuid = %s AND example_number = %s;''',
            (mark, time_to_rate_example, poll_uuid, example_number,)
        )

    elif question_type == ExampleQuestionsStates.AskAboutSourceTimbreSimilarity:
        cur.execute(
            ''' UPDATE survey_results 
                SET source_timbre_similarity = %s, source_timbre_similarity_time_taken = %s 
                WHERE poll_uuid = %s AND example_number = %s;''',
            (mark, time_to_rate_example, poll_uuid, example_number,)
        )

        if source_instrument_name == target_instrument_name:
            record_answer(conn=conn,
                          poll_uuid=poll_uuid,
                          example_audio=example_audio,
                          example_number=example_number,
                          question_type=ExampleQuestionsStates.AskAboutTargetTimbreSimilarity,
                          mark=mark,
                          time_to_rate_example=time_to_rate_example)

    elif question_type == ExampleQuestionsStates.AskAboutTargetTimbreSimilarity:
        cur.execute(
            ''' UPDATE survey_results 
                SET target_timbre_similarity = %s, target_timbre_similarity_time_taken = %s 
                WHERE poll_uuid = %s AND example_number = %s;''',
            (mark, time_to_rate_example, poll_uuid, example_number,)
        )

    conn.commit()
    cur.close()
