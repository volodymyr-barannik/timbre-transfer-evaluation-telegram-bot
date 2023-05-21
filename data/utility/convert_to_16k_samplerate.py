import os
from pydub import AudioSegment


def resample_audio_file(filepath):
    # Load the .wav file
    audio = AudioSegment.from_wav(filepath)

    # Check if the sample rate is not 16k
    if audio.frame_rate != 16000:
        # If not, resample it to 16k
        audio = audio.set_frame_rate(16000)

        # Save it back to the same file, effectively overwriting the original
        audio.export(filepath, format="wav")


def resample_wav_files_in_dir(directory):
    for foldername, subfolders, filenames in os.walk(directory):
        for filename in filenames:
            if filename.endswith('.wav'):
                filepath = os.path.join(foldername, filename)
                resample_audio_file(filepath)


# Call the function on the root directory
# resample_wav_files_in_dir('E:\\Code\\TimbreTransfer_ExperimentExamples\\DDSP\\ddspcopy')