import os
import numpy as np
from scipy.io import wavfile

import os
import numpy as np
from scipy.io import wavfile


def normalize_audio_file(filepath, new_filepath):
    # Read the .wav file
    rate, data = wavfile.read(filepath)

    # Normalize the data
    float_data = data.astype(np.float32)
    normalized_data = np.interp(float_data, (float_data.min(), float_data.max()), (-32768, 32767))

    # Write the normalized data to a new .wav file
    wavfile.write(new_filepath, rate, normalized_data.astype(np.int16))


def normalize_wav_files_in_dir(directory):
    for foldername, subfolders, filenames in os.walk(directory):
        for filename in filenames:
            if filename.endswith('.wav'):
                filepath = os.path.join(foldername, filename)
                new_filepath = os.path.splitext(filepath)[0] + '_n.wav'
                normalize_audio_file(filepath, new_filepath)

# normalize_wav_files_in_dir('E:\\Code\\TimbreTransfer_ExperimentExamples\\DDSP\\ddsp_vst2')
