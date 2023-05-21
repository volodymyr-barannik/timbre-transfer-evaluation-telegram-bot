import textwrap
from collections import defaultdict
from pprint import pprint
from textwrap import wrap

import psycopg2

import platform
import sys
import time
import uuid
from enum import Enum

from plotly.subplots import make_subplots

if platform.system() == 'Windows':
    original_midi_ddsp_module_path = 'E:/Code/Projects/TimbreTransfer/original-midi-ddsp/'
    original_ddsp_module_path = 'E:/Code/Projects/TimbreTransfer/original-ddsp-for-vst-debugging/'


def apply_module_path(module_path):
    print(f"module_path={module_path}")
    if module_path not in sys.path:
        sys.path.append(module_path)
        print(f"appending {module_path} to sys.path")
    else:
        print(f"do not appending {module_path} to sys.path")


# It should always be on top!
apply_module_path(original_ddsp_module_path)
apply_module_path(original_midi_ddsp_module_path)


from data.postgresql.elo.frontend.secret import *
import plotly.graph_objects as go


def get_elo(cur):
    # Execute the query
    cur.execute("""
        SELECT e1.model_path, e1.model_title, e1.training_dataset, er.example1_score, 
        e2.model_path, e2.model_title, e2.training_dataset, er.example2_score 
        FROM elo_record er
        INNER JOIN examples e1 ON er.example1_id = e1.example_id
        INNER JOIN examples e2 ON er.example2_id = e2.example_id
    """)

    elo_ratings = defaultdict(lambda: 300)  # Starting ELO rating for each model is 1000
    k_factor = 32

    for record in cur:
        model_path1, model_title1, dataset1, score1, model_path2, model_title2, dataset2, score2 = record
        pair1 = (model_path1, model_title1, dataset1)
        pair2 = (model_path1, model_title2, dataset2)

        rating1 = elo_ratings[pair1]
        rating2 = elo_ratings[pair2]

        # Calculate expected scores
        expected1 = 1 / (1 + pow(10, (rating2 - rating1) / 400))
        expected2 = 1 / (1 + pow(10, (rating1 - rating2) / 400))

        # Update ratings
        elo_ratings[pair1] = rating1 + k_factor * (score1 - expected1)
        elo_ratings[pair2] = rating2 + k_factor * (score2 - expected2)

    return elo_ratings


# Open a cursor to perform database operations
cur = conn.cursor()

question_types = ['sound_quality', 'timbre_similarity_source', 'timbre_similarity_target']


fig = make_subplots(rows=3, cols=1, subplot_titles=question_types)

for idx, question_type in enumerate(question_types, start=1):

    # Execute the query to get number of wins or 'both good'
    cur.execute("""
        SELECT e1.model_path, e1.model_title, e1.training_dataset, SUM(CASE WHEN er.example1_score >= er.example2_score AND er.example1_score != 0 THEN 1 ELSE 0 END) AS wins
        FROM elo_record er
        INNER JOIN examples e1 ON er.example1_id = e1.example_id
        WHERE er.question_type = %s
        GROUP BY e1.model_path, e1.model_title, e1.training_dataset
        UNION ALL
        SELECT e2.model_path, e2.model_title, e2.training_dataset, SUM(CASE WHEN er.example2_score >= er.example1_score AND er.example2_score != 0 THEN 1 ELSE 0 END) AS wins
        FROM elo_record er
        INNER JOIN examples e2 ON er.example2_id = e2.example_id
        WHERE er.question_type = %s
        GROUP BY e2.model_path, e2.model_title, e2.training_dataset;
    """, (question_type, question_type))

    wins_or_same_count = defaultdict(int)

    for record in cur:
        model_path, model_title, training_dataset, wins = record
        pair = (model_path, model_title, training_dataset)
        wins_or_same_count[pair] += wins


    # Execute the query to get number of 100% wins
    cur.execute("""
        SELECT e1.model_path, e1.model_title, e1.training_dataset, SUM(CASE WHEN er.example1_score > er.example2_score THEN 1 ELSE 0 END) AS wins
        FROM elo_record er
        INNER JOIN examples e1 ON er.example1_id = e1.example_id
        WHERE er.question_type = %s
        GROUP BY e1.model_path, e1.model_title, e1.training_dataset
        UNION ALL
        SELECT e2.model_path, e2.model_title, e2.training_dataset, SUM(CASE WHEN er.example2_score > er.example1_score THEN 1 ELSE 0 END) AS wins
        FROM elo_record er
        INNER JOIN examples e2 ON er.example2_id = e2.example_id
        WHERE er.question_type = %s
        GROUP BY e2.model_path, e2.model_title, e2.training_dataset;
    """, (question_type, question_type))

    wins_count = defaultdict(int)

    for record in cur:
        model_path, model_title, training_dataset, wins = record
        pair = (model_path, model_title, training_dataset)
        wins_count[pair] += wins


    # Execute the query to get total appearances
    cur.execute("""
        SELECT e1.model_path, e1.model_title, e1.training_dataset, COUNT(*) AS appearances 
        FROM elo_record er
        INNER JOIN examples e1 ON er.example1_id = e1.example_id
        WHERE er.question_type = %s
        GROUP BY e1.model_path, e1.model_title, e1.training_dataset
        UNION ALL
        SELECT e2.model_path, e2.model_title, e2.training_dataset, COUNT(*) AS appearances 
        FROM elo_record er
        INNER JOIN examples e2 ON er.example2_id = e2.example_id
        WHERE er.question_type = %s
        GROUP BY e2.model_path, e2.model_title, e2.training_dataset;
    """, (question_type, question_type))

    appearances_count = {}

    for record in cur:
        model_path, model_title, training_dataset, appearances = record
        pair = (model_path, model_title, training_dataset)
        appearances_count[pair] = appearances

    # elo_ratings = get_elo(cur)

    print('wins_or_same_count=')
    pprint(wins_or_same_count)
    print()
    print()
    print('wins_count=')
    pprint(wins_count)
    print()
    print()
    print('appearances_count=')
    pprint(appearances_count)

    wrapper = textwrap.TextWrapper(width=10)  # You can adjust the width as needed

    def get_names_for_keys(keys):
        return [wrapper.fill(f'{model_title}'
                f'\n{training_dataset}').replace('\n', '<br>') for model_path, model_title, training_dataset in keys]

    print(f'names for keys: {get_names_for_keys(list(appearances_count.keys()))}')

    print(len(appearances_count))
    print(len(wins_count))

    assert(len(appearances_count) == len(wins_count))

    number_of_wins_to_appearances = {kw: vw/va for (kw, vw), (ka, va) in zip(wins_count.items(), appearances_count.items())}

    # Create a plotly bar chart
    fig.add_trace(go.Bar(name='Total Appearances',
               x=get_names_for_keys(list(appearances_count.keys())),
               y=list(appearances_count.values()),
               marker_color='#9cc2ff'),
               row=idx, col=1)

    fig.add_trace(go.Bar(name='Wins',
               x=get_names_for_keys(list(wins_count.keys())),
               y=list(wins_count.values()),
               marker_color='orange', opacity=1),
               row=idx, col=1)

    # fig.add_trace(go.Bar(name='number_of_wins_to_appearances',
    #            x=get_names_for_keys(list(number_of_wins_to_appearances.keys())),
    #            y=list(number_of_wins_to_appearances.values()),
    #            marker_color='red', opacity=1),
    #            row=idx, col=1)

    # fig.add_trace(go.Bar(name='Elo rating',
    #            x=get_names_for_keys(list(elo_ratings.keys())),
    #            y=list(elo_ratings.values()),
    #            marker_color='red', opacity=1),
    #            row=idx, col=1)

    # fig.add_trace(go.Bar(name='Wins or both good',
    #           x=get_names_for_keys(list(wins_or_same_count.keys())),
    #           y=list(wins_or_same_count.values()),
    #           marker_color='yellow', opacity=0.5),
    #           row=idx, col=1)


# Change the bar mode
fig.update_layout(width=1920, height=1080,
                  barmode='overlay',
                  title_text=f'Number of Wins and Total Appearances per Question Type.',
                  xaxis_title='Pair (model_path, training_dataset)',
                  yaxis_title='Count',)

# Display the plot
fig.show()

# Close communication with the database
cur.close()
conn.close()