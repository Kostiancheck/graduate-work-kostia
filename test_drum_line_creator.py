import glob
import mido
import numpy

midi_files = glob.glob("groove-v1.0.0-midionly/groove" + '/**/*.mid', recursive=True)
midi_file_test = mido.MidiFile(midi_files[0], clip=True)
print(midi_file_test)
