import psycopg2

from data.local_drive import TimbreTransferAudioExample
from data.postgresql.secrets import PG_DB_NAME, PG_DB_PASSWORD, PG_DB_USERNAME

pg_conn = psycopg2.connect(
    dbname=PG_DB_NAME,
    user=PG_DB_USERNAME,
    password=PG_DB_PASSWORD,
    host="localhost",
    port="5432"
)


def record_user_data(user_id: int, username: str, user_first_name: str):
    conn = pg_conn
    cur = conn.cursor()

    # Insert user if not exists
    cur.execute("SELECT * FROM public.users WHERE user_id = %s", (user_id,))
    result = cur.fetchone()

    if result is None:  # If user is not already in the database, insert them
        cur.execute("INSERT INTO public.users(user_id, username, user_first_name) VALUES (%s, %s, %s)",
                    (user_id, username, user_first_name))

    conn.commit()
    cur.close()


def record_example_data(example_audio: TimbreTransferAudioExample) -> int:
    conn = pg_conn
    cur = conn.cursor()

    # Insert example if not exists
    cur.execute("SELECT * FROM public.examples WHERE model_path = %s AND source_instrument = %s AND target_instrument = %s",
                (example_audio.src_folder.folder_path, example_audio.source_instrument_name,
                 example_audio.target_instrument_name,))
    result = cur.fetchone()

    if result is None:  # If example is not already in the database, insert it
        cur.execute("INSERT INTO public.examples(model_title, model_path, training_dataset, source_instrument, target_instrument) \
                     VALUES (%s, %s, %s, %s, %s) RETURNING example_id",
                    (example_audio.src_folder.title, example_audio.src_folder.folder_path,
                     example_audio.src_folder.training_dataset,
                     example_audio.source_instrument_name, example_audio.target_instrument_name))
        example_id = cur.fetchone()[0]
    else:
        example_id = result[0]

    conn.commit()
    cur.close()

    return example_id


def record_response_data(poll_uuid: str,
                         chat_id: int,
                         user_id: int,
                         example_number: int,

                         question_type: str,
                         first_example_id: int,
                         first_score: int,
                         second_example_id: int,
                         second_score: int,
                         elapsed_time: float,):

    conn = pg_conn
    cur = conn.cursor()

    # Insert a new elo record
    cur.execute("INSERT INTO public.elo_record(question_type, example1_id, example2_id, example1_score, example2_score) \
                 VALUES (%s, %s, %s, %s, %s) RETURNING elo_record_id",
                (question_type, first_example_id, second_example_id, first_score, second_score))

    elo_record_id = cur.fetchone()[0]

    # Insert a new response
    cur.execute("INSERT INTO public.responses(poll_uuid, chat_id, user_id, example_number, elo_record_id, time_elapsed) \
                 VALUES (%s, %s, %s, %s, %s, %s)",
                (poll_uuid, chat_id, user_id, example_number, elo_record_id, elapsed_time))

    conn.commit()
    cur.close()


def get_n_elo_records() -> int:
    conn = pg_conn
    cur = conn.cursor()

    # Insert user if not exists
    cur.execute("SELECT COUNT(*) FROM elo_record;")
    result = cur.fetchone()

    conn.commit()
    cur.close()

    return result
