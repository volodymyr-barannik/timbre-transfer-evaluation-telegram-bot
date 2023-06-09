import logging
import os
import random
from enum import Enum
from typing import Optional

import original_midi_ddsp

BASE_FOLDER_MIDI_DDSP_PATH = 'E:\\Code\\TimbreTransfer_ExperimentExamples\\MIDI_DDSP\\auto'
BASE_FOLDER_DDSP_PATH = 'E:\\Code\\TimbreTransfer_ExperimentExamples\\DDSP\\'
BASE_FOLDER_REFERENCE_PATH = 'E:\\Code\\TimbreTransfer_ExperimentExamples\\REFERENCE\\'
OUT_WILDCARD = '_out_n.wav'
IN_WILDCARD = '_in_n.wav'


class AudioSourceFolder(object):

    def __init__(self, title, dataset, target_instrument, folder_path, filename_wildcard):
        self.title = title
        self.training_dataset = dataset
        self.target_instrument = target_instrument

        self.folder_path = folder_path
        self.filename_wildcard = filename_wildcard

    def full(self):
        return os.path.join(self.folder_path, self.filename_wildcard)

    def is_same_as(self, other):
        return self.title == other.title and \
               self.training_dataset == other.training_dataset and \
               self.target_instrument == other.target_instrument and \
               self.folder_path == other.folder_path and \
               self.filename_wildcard == other.filename_wildcard

    def __str__(self):
        return f'title={self.title}, training_dataset={self.training_dataset}, self.target_instrument={self.target_instrument},' \
               f'\n folder_path={self.folder_path}, filename_wildcard={self.filename_wildcard}'


class AudioExampleInstrumentType(Enum):
    SourceInstrument = 1
    TargetInstrument = 2


class TimbreTransferAudioExample(object):

    def __init__(self, src_folder: AudioSourceFolder, in_example_path: str, out_example_path: str):
        self.src_folder: AudioSourceFolder = src_folder
        self.path = out_example_path

        self.source_instrument_name: str = self.get_instrument_name_from_filename(in_example_path)
        self.target_instrument_name: str = self.get_instrument_name_from_filename(out_example_path)
        if self.target_instrument_name == 'same':
            self.target_instrument_name = self.source_instrument_name

    def get_instrument_abb_from_filename(self, filename):
        return os.path.basename(filename).split('_')[1]

    def get_instrument_name_from_filename(self, filename):
        abb = self.get_instrument_abb_from_filename(filename)
        if abb == 'None':
            return 'same'
        else:
            return original_midi_ddsp.data_handling.instrument_name_utils.INST_ABB_TO_NAME_DICT[abb]

    def __str__(self):
        return f'{self.source_instrument_name} -> {self.target_instrument_name}, \n' \
               f'ds: {self.src_folder.training_dataset}, \n' \
               f'path: {self.src_folder.folder_path}'

    def get_instrument_by_type(self, instrument_type: AudioExampleInstrumentType):
        res: Optional[str] = None
        if instrument_type == AudioExampleInstrumentType.SourceInstrument:
            res = self.source_instrument_name
        elif instrument_type == AudioExampleInstrumentType.TargetInstrument:
            res = self.target_instrument_name
        else:
            raise Exception()

        return res


class AudioDatasetPerFolder(object):

    def __init__(self, src_folder: AudioSourceFolder):
        self.src_folder: AudioSourceFolder = src_folder

        self.examples_list: [TimbreTransferAudioExample] = self.get_examples_from_folder(self.src_folder)

        if len(self.examples_list) == 0:
            logging.warning(f'AudioDatasetPerFolder loaded an empty dataset! Is it intended?'
                            f'\nsrc_folder: \n{str(src_folder)}')


    def get_examples_from_folder(self, src_folder):
        folder = src_folder.folder_path

        outs = [os.path.join(folder, f) for f in os.listdir(folder) if f.endswith(OUT_WILDCARD)]
        ins = [os.path.join(folder, f) for f in os.listdir(folder) if f.endswith(IN_WILDCARD)]

        all_matching_files_pairs_in_folder = [(in_f, out_f) for in_f, out_f in zip(ins, outs)]

        examples: [TimbreTransferAudioExample] = []
        for example_in_path, example_out_path in all_matching_files_pairs_in_folder:
            example = TimbreTransferAudioExample(src_folder=src_folder,
                                                 in_example_path=example_in_path,
                                                 out_example_path=example_out_path)

            examples.append(example)

        def get_example_index_from_filename(example: TimbreTransferAudioExample):
            idx = int(os.path.basename(example.path).split('_')[0])
            return idx

        examples = sorted(examples, key=get_example_index_from_filename)

        return examples

    def get_random_batch(self, size):
        return random.sample(self.examples_list, size)

    def get_by_source_instrument(self, source_instrument_name) -> [TimbreTransferAudioExample]:
        return [ex for ex in self.examples_list if ex.source_instrument_name == source_instrument_name]

    def get_by_target_instrument(self, target_instrument_name) -> [TimbreTransferAudioExample]:
        return [ex for ex in self.examples_list if ex.target_instrument_name == target_instrument_name]


class AudioDatasetPerFolderCollection(object):

    def __init__(self, datasets: [AudioDatasetPerFolder]):

        self.datasets: [AudioDatasetPerFolder] = datasets

    def pick_random_audio_example(self) -> TimbreTransferAudioExample:
        random_dataset: AudioDatasetPerFolder = random.sample(self.datasets, 1)[0]
        random_example: TimbreTransferAudioExample = random.sample(random_dataset.examples_list, 1)[0]

        return random_example

    def pick_random_audio_example_by_predicate(self, predicate) -> Optional[TimbreTransferAudioExample]:
        examples_with_our_source_instrument = []

        i: int = 0
        while len(examples_with_our_source_instrument) == 0:

            random_dataset: AudioDatasetPerFolder = random.sample(self.datasets, 1)[0]

            if i > 10:
                logging.debug(f'Picking random audio example by predicate takes too long. '
                                f'\nCandidate: {str(random_dataset.src_folder)}')

            if i > 100:
                logging.warning(f'Picking random audio example by predicate takes very long. '
                                f'\nCandidate: {str(random_dataset.src_folder)}')

                raise Exception()

            examples_with_our_source_instrument = [ex for ex in random_dataset.examples_list
                                                   if predicate(ex)]

            i = i+1

        random_example: TimbreTransferAudioExample = random.sample(examples_with_our_source_instrument, 1)[0]

        return random_example
