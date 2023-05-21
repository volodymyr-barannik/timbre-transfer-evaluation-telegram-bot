import os

from data.local_drive import AudioSourceFolder, BASE_FOLDER_MIDI_DDSP_PATH, OUT_WILDCARD, IN_WILDCARD, \
    BASE_FOLDER_DDSP_PATH, \
    BASE_FOLDER_REFERENCE_PATH, AudioDatasetPerFolder, AudioDatasetPerFolderCollection

EVAL_AUDIO_SOURCES = [

    AudioSourceFolder(title='Input (gt)', dataset='all', target_instrument='vn',
                      folder_path=os.path.join(BASE_FOLDER_MIDI_DDSP_PATH, 'inputs_gt'),
                      filename_wildcard=IN_WILDCARD),
    
    AudioSourceFolder(title='Magenta DDSP-VST to vn', dataset='?', target_instrument='vn',
                      folder_path=os.path.join(BASE_FOLDER_DDSP_PATH, 'ddsp_vst2'),
                      filename_wildcard=OUT_WILDCARD),

    AudioSourceFolder(title='Magenta DDSP to vn', dataset='?', target_instrument='vn',
                      folder_path=os.path.join(BASE_FOLDER_DDSP_PATH, 'ddsp16khz'),
                      filename_wildcard=OUT_WILDCARD),

    AudioSourceFolder(title='Magenta MIDI-DDSP to vn', dataset='all', target_instrument='vn',
                      folder_path=os.path.join(BASE_FOLDER_MIDI_DDSP_PATH, 'magenta_midi_ddsp_all'),
                      filename_wildcard=OUT_WILDCARD),

    AudioSourceFolder(title='Our MIDI-DDSP to vn', dataset='vn', target_instrument='vn',
                      folder_path=os.path.join(BASE_FOLDER_MIDI_DDSP_PATH, 'my_midi_ddsp_vn'),
                      filename_wildcard=OUT_WILDCARD),


    AudioSourceFolder(title='Magenta SynthCoder to oboe', dataset='all', target_instrument='oboe',
                      folder_path=os.path.join(BASE_FOLDER_MIDI_DDSP_PATH, 'magenta_midi_ddsp_all_sc_to_oboe'),
                      filename_wildcard=OUT_WILDCARD),

    AudioSourceFolder(title='Magenta SynthCoder to same', dataset='all', target_instrument='same',
                      folder_path=os.path.join(BASE_FOLDER_MIDI_DDSP_PATH, 'magenta_midi_ddsp_all_sc_to_same'),
                      filename_wildcard=OUT_WILDCARD),

    AudioSourceFolder(title='Magenta SynthCoder to vn', dataset='all', target_instrument='vn',
                      folder_path=os.path.join(BASE_FOLDER_MIDI_DDSP_PATH, 'magenta_midi_ddsp_all_sc_to_vn'),
                      filename_wildcard=OUT_WILDCARD),


    AudioSourceFolder(title='Our SynthCoder without Mel to vn', dataset='all', target_instrument='vn',
                      folder_path=os.path.join(BASE_FOLDER_MIDI_DDSP_PATH, 'midi_ddsp_no_mel_all'),
                      filename_wildcard=OUT_WILDCARD),
]

# We give it to listeners to evaluate
EVAL_AUDIO_DATASETS = [AudioDatasetPerFolder(src_folder=src_folder) for src_folder in EVAL_AUDIO_SOURCES]
EVAL_AUDIO_DATASETS_COLLECTION = AudioDatasetPerFolderCollection(datasets=EVAL_AUDIO_DATASETS)

# To show how some instruments sound in real life, just for reference.
# Somebody could be unfamiliar with some instruments
REFERENCE_AUDIO_SOURCES = [

    AudioSourceFolder(title='Reference (gt)', dataset='all', target_instrument='same',
                      folder_path=BASE_FOLDER_REFERENCE_PATH,
                      filename_wildcard=IN_WILDCARD),

]

REFERENCE_AUDIO_DATASETS = [AudioDatasetPerFolder(src_folder=src_folder) for src_folder in REFERENCE_AUDIO_SOURCES]
REFERENCE_AUDIO_DATASETS_COLLECTION = AudioDatasetPerFolderCollection(datasets=REFERENCE_AUDIO_DATASETS)
