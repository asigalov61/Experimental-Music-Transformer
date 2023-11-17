# -*- coding: utf-8 -*-
"""Experimental_Music_Transformer_Training_Dataset_Maker.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/github/asigalov61/Experimental-Music-Transformer/blob/main/Training-Data/Experimental_Music_Transformer_Training_Dataset_Maker.ipynb

# Experimental Music Transformer Training Dataset Maker (ver. 1.0)

***

Powered by tegridy-tools: https://github.com/asigalov61/tegridy-tools

***

#### Project Los Angeles

#### Tegridy Code 2023

***

# (SETUP ENVIRONMENT)
"""

#@title Install all dependencies (run only once per session)

!git clone https://github.com/asigalov61/tegridy-tools
!pip install tqdm

#@title Import all needed modules

print('Loading needed modules. Please wait...')
import os
import copy
import math
import statistics
import random

from tqdm import tqdm

if not os.path.exists('/content/Dataset'):
    os.makedirs('/content/Dataset')

print('Loading TMIDIX module...')
os.chdir('/content/tegridy-tools/tegridy-tools')

import TMIDIX

from joblib import Parallel, delayed

print('Done!')

os.chdir('/content/')
print('Enjoy! :)')

"""# (DOWNLOAD SOURCE MIDI DATASET)"""

# Commented out IPython magic to ensure Python compatibility.
#@title Download original LAKH MIDI Dataset

# %cd /content/Dataset/

!wget 'http://hog.ee.columbia.edu/craffel/lmd/lmd_full.tar.gz'
!tar -xvf 'lmd_full.tar.gz'
!rm 'lmd_full.tar.gz'

# %cd /content/

#@title Mount Google Drive
from google.colab import drive
drive.mount('/content/drive')

"""# (FILE LIST)"""

#@title Save file list
###########

print('Loading MIDI files...')
print('This may take a while on a large dataset in particular.')

dataset_addr = "/content/Dataset"
# os.chdir(dataset_addr)
filez = list()
for (dirpath, dirnames, filenames) in os.walk(dataset_addr):
    filez += [os.path.join(dirpath, file) for file in filenames]
print('=' * 70)

if filez == []:
    print('Could not find any MIDI files. Please check Dataset dir...')
    print('=' * 70)

print('Randomizing file list...')
random.shuffle(filez)

TMIDIX.Tegridy_Any_Pickle_File_Writer(filez, '/content/drive/MyDrive/filez')

#@title Load file list
filez = TMIDIX.Tegridy_Any_Pickle_File_Reader('/content/drive/MyDrive/filez')

"""# (PROCESS)"""

#@title Process MIDIs with TMIDIX MIDI processor

#===============================================================================

def TMIDIX_MIDI_Processor(midi_file):

    melody_chords = []
    melody_chords_aug = []

    try:

        fn = os.path.basename(midi_file)

        # Filtering out EXP MIDIs
        file_size = os.path.getsize(midi_file)

        if file_size <= 1000000:

          #=======================================================
          # START PROCESSING

          # Convering MIDI to ms score with MIDI.py module
          score = TMIDIX.midi2single_track_ms_score(open(midi_file, 'rb').read(), recalculate_channels=False, pass_old_timings_events=True)

          # INSTRUMENTS CONVERSION CYCLE
          events_matrix = []
          itrack = 1
          patches = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]

          emphasis_time = 0
          emph_once = False

          tpq = 0
          tempo = 0
          time_sig = 0
          key_sig = 0

          while itrack < len(score):
              for event in score[itrack]:

                  if event[0] != 'note':
                    event.extend([0, 128])
                  else:
                    event.extend([0])

                  if event[0] == 'text_event' or event[0] == 'lyric' or event[0] == 'patch_change':
                    event[4] = 128

                  events_matrix.append(event)

              itrack += 1

          events_matrix.sort(key=lambda x: x[4], reverse = True)
          events_matrix.sort(key=lambda x: x[1])

          events_matrix1 = []

          for event in events_matrix:
                  if event[0] == 'patch_change':
                        patches[event[2]] = event[3]

                  #========================================================================
                  # Emphasis

                  if event[0] == 'text_event' or event[0] == 'lyric':
                        emphasis_time = event[1]
                        emph_once = True

                  if event[0] == 'note' and int(event[1] / 8) == int(emphasis_time / 8) and emph_once:
                        event.extend([1])
                        emph_once = False
                  else:
                        event.extend([0])

                  #========================================================================
                  # Tempo

                  if event[0] == 'old_tpq':
                        tpq = event[2]

                  if event[0] == 'old_set_tempo':
                        tempo = event[2]

                  #========================================================================
                  # Time and key sigs

                  if event[0] == 'time_signature':
                        time_sig = round((event[2] / event[3]) * 10)

                  if event[0] == 'key_signature':
                        key_sig = (event[3] * 16) + event[2]+8

                  #========================================================================
                  # Notes

                  if event[0] == 'note':
                        event[6] = patches[event[3]]
                        event.extend([round(tempo / tpq / 100)])
                        event.extend([time_sig])
                        event.extend([key_sig])

                        if events_matrix1:
                            if (event[1] == events_matrix1[-1][1]):
                                if ([event[3], event[4]] != events_matrix1[-1][3:5]):
                                    events_matrix1.append(event)
                            else:
                                events_matrix1.append(event)

                        else:
                            events_matrix1.append(event)

        if len(events_matrix1) > 0:
            if min([e[1] for e in events_matrix1]) >= 0 and min([e[2] for e in events_matrix1]) >= 0:

                #=======================================================
                # PRE-PROCESSING

                # checking number of instruments in a composition
                instruments_list_without_drums = list(set([y[3] for y in events_matrix1 if y[3] != 9]))
                instruments_list = list(set([y[3] for y in events_matrix1]))

                if len(events_matrix1) > 0 and len(instruments_list_without_drums) > 0:

                    num_karaoke_events = len([y for y in events_matrix if y[0] == 'text_event' or y[0] == 'lyric'])

                    # checking number of karaoke events in a composition
                    if num_karaoke_events >= 100:

                      #=======================================================
                      # MAIN PROCESSING
                      #=======================================================

                      #=======================================================
                      # Timings
                      #=======================================================

                      events_matrix2 = []

                      # Recalculating timings
                      for e in events_matrix1:

                          ev = copy.deepcopy(e)

                          # Original timings
                          e[1] = int(e[1] / 8)
                          e[2] = int(e[2] / 8)

                          # Augmented timings (+ 5%)
                          ev[1] = int((ev[1] * 1.05) / 8)
                          ev[2] = int((ev[2] * 1.05) / 8)

                          events_matrix2.append(ev)

                      #===================================
                      # ORIGINAL COMPOSITION
                      #===================================

                      # Sorting by patch, pitch, then by start-time

                      events_matrix1.sort(key=lambda x: x[6])
                      events_matrix1.sort(key=lambda x: x[4], reverse=True)
                      events_matrix1.sort(key=lambda x: x[1])

                      #=======================================================
                      # FINAL PROCESSING

                      melody_chords = []

                      # Break between compositions / Intro seq

                      if 9 in instruments_list:
                          drums_present = 8852 # Yes
                      else:
                          drums_present = 8851 # No

                      if events_matrix1[0][3] != 9:
                          pat = events_matrix1[0][6] // 8
                      else:
                          pat = 16

                      ptc = events_matrix1[0][4]

                      melody_chords.extend([8998, drums_present, 8853+pat, 8870+ptc]) # Intro seq

                      #=======================================================
                      # PROCESSING CYCLE
                      #=======================================================

                      abs_time = 0

                      pbar_time = 0

                      pe = events_matrix1[0]

                      chords_counter = 1

                      time_key_seq = [0, 0, 0]
                      old_time_key_seq = [0, 0, 0]

                      tempo = 0
                      time_sig = 0
                      key_sig = 0

                      comp_chords_len = len(list(set([y[1] for y in events_matrix1])))

                      for e in events_matrix1:

                          #=======================================================
                          # Timings...

                          # Cliping all values...
                          delta_time = max(0, min(511, e[1]-pe[1]))
                          abs_time += delta_time

                          bar_time = abs_time // 512
                          bar_time_local = abs_time % 512

                          if bar_time >= 1024:
                              break

                          # Durations and channels

                          dur = max(0, min(511, e[2]))
                          cha = max(0, min(15, e[3]))

                          # Patches
                          if cha == 9: # Drums patch will be == 16
                              pat = 16

                          else:
                              pat = e[6] // 8

                          # Pitches
                          ptc = max(1, min(127, e[4]))


                          # Emphasis
                          emph = e[7]

                          # Velocities
                          # Calculating octo-velocity
                          vel = max(8, min(127, e[5]))
                          velocity = round(vel / 15)-1

                          #=======================================================
                          # Outro seq

                          if ((comp_chords_len - chords_counter) == 50) and (delta_time != 0):
                              out_t = 7810+delta_time
                              out_p = 8322+ptc
                              melody_chords.extend([8850, 8850, out_t, out_p]) # outro seq

                          #=======================================================

                          if time_key_seq[0] != e[8]: # Tempo
                            time_key_seq[0] = e[8]

                          if time_key_seq[1] != e[9]: # Time sig
                            time_key_seq[1] = e[9]

                          if time_key_seq[2] != e[10]: # Key sig
                            time_key_seq[2] = e[10]

                          if time_key_seq != old_time_key_seq:

                            old_time_key_seq = time_key_seq

                            time_key_seq[0] = max(254, time_key_seq[0]) + 8451
                            time_key_seq[1] = max(128, time_key_seq[1]) + 8706
                            time_key_seq[2] = max(16, time_key_seq[2]) + 8834

                            melody_chords.extend([8450] + time_key_seq)

                          #=======================================================
                          # Bar counter seq

                          if (bar_time > pbar_time) and (delta_time != 0):
                              bar = 6786+min(1023, (bar_time)) # bar counter seq
                              bar_t = 7810+bar_time_local
                              bar_p = 8322+ptc
                              melody_chords.extend([6786, bar, bar_t, bar_p])
                              chords_counter += 1
                              pbar_time = bar_time

                          else:
                              if delta_time != 0:
                                  chords_counter += 1

                          #=======================================================
                          # FINAL NOTE SEQ

                          # Writing final note asynchronously

                          dur_vel = (8 * dur) + velocity
                          pat_ptc = (128 * pat) + ptc

                          melody_chords.extend([emph+6784, delta_time, dur_vel+512, pat_ptc+4608])

                          pe = e

                          #=======================================================

                      melody_chords.extend([8999, 8999, 8999, 8999]) # EOS

                      #===================================
                      # AUGMENTED COMPOSITION
                      #===================================

                      # Sorting by patch, pitch, then by start-time

                      events_matrix2.sort(key=lambda x: x[6])
                      events_matrix2.sort(key=lambda x: x[4], reverse=True)
                      events_matrix2.sort(key=lambda x: x[1])

                      # Simple pitches augmentation

                      ptc_shift = 1 # Shifting up by 1 semi-tone

                      for e in events_matrix2:
                          if e[3] != 9:
                              e[4] = e[4] + ptc_shift

                      #=======================================================
                      # FINAL PROCESSING

                      melody_chords_aug = []

                      # Break between compositions / Intro seq

                      if 9 in instruments_list:
                          drums_present = 8852 # Yes
                      else:
                          drums_present = 8851 # No

                      if events_matrix2[0][3] != 9:
                          pat = events_matrix2[0][6] // 8
                      else:
                          pat = 16

                      ptc = events_matrix2[0][4]

                      melody_chords_aug.extend([8998, drums_present, 8853+pat, 8870+ptc]) # Intro seq

                      #=======================================================
                      # PROCESSING CYCLE
                      #=======================================================

                      abs_time = 0

                      pbar_time = 0

                      pe = events_matrix2[0]

                      chords_counter = 1

                      time_key_seq = [0, 0, 0]
                      old_time_key_seq = [0, 0, 0]

                      tempo = 0
                      time_sig = 0
                      key_sig = 0

                      comp_chords_len = len(list(set([y[1] for y in events_matrix2])))

                      for e in events_matrix2:

                          #=======================================================
                          # Timings...

                          # Cliping all values...
                          delta_time = max(0, min(511, e[1]-pe[1]))
                          abs_time += delta_time

                          bar_time = abs_time // 512
                          bar_time_local = abs_time % 512

                          if bar_time >= 1024:
                              break

                          # Durations and channels

                          dur = max(0, min(511, e[2]))
                          cha = max(0, min(15, e[3]))

                          # Patches
                          if cha == 9: # Drums patch will be == 128
                              pat = 16

                          else:
                              pat = e[6] // 8

                          # Pitches
                          ptc = max(1, min(127, e[4]))

                          # Emphasis
                          emph = e[7]

                          # Velocities
                          # Calculating octo-velocity
                          vel = max(8, min(127, e[5]-4))
                          velocity = round(vel / 15)-1

                          #=======================================================
                          # Outro seq

                          if ((comp_chords_len - chords_counter) == 50) and (delta_time != 0):
                              out_t = 7810+delta_time
                              out_p = 8322+ptc
                              melody_chords_aug.extend([8850, 8850, out_t, out_p]) # outro seq

                          #=======================================================

                          if time_key_seq[0] != e[8]: # Tempo
                            time_key_seq[0] = e[8]

                          if time_key_seq[1] != e[9]: # Time sig
                            time_key_seq[1] = e[9]

                          if time_key_seq[2] != e[10]: # Key sig
                            time_key_seq[2] = e[10]

                          if time_key_seq != old_time_key_seq:
                            old_time_key_seq = time_key_seq

                            time_key_seq[0] = max(254, time_key_seq[0]) + 8451
                            time_key_seq[1] = max(128, time_key_seq[1]) + 8706
                            time_key_seq[2] = max(16, time_key_seq[2]) + 8834

                            melody_chords_aug.extend([8450] + time_key_seq)

                          #=======================================================
                          # Bar counter seq

                          if (bar_time > pbar_time) and (delta_time != 0):
                              bar = 6786+min(1023, (bar_time)) # bar counter seq
                              bar_t = 7810+bar_time_local
                              bar_p = 8322+ptc
                              melody_chords_aug.extend([6786, bar, bar_t, bar_p])
                              chords_counter += 1
                              pbar_time = bar_time

                          else:
                              if delta_time != 0:
                                  chords_counter += 1

                          #=======================================================
                          # FINAL NOTE SEQ

                          # Writing final note asynchronously

                          dur_vel = (8 * dur) + velocity
                          pat_ptc = (128 * pat) + ptc

                          melody_chords_aug.extend([emph+6784, delta_time, dur_vel+512, pat_ptc+4608])

                          pe = e

                      #=======================================================

                      melody_chords_aug.extend([8999, 8999, 8999, 8999]) # EOS

                      #=======================================================

                      # TOTAL DICTIONARY SIZE 8999+1=9000

                      #=======================================================

                      return melody_chords, melody_chords_aug

    except Exception as ex:
        print('WARNING !!!')
        print('=' * 70)
        print('Bad MIDI:', f)
        print('Error detected:', ex)
        print('=' * 70)
        return None

#===============================================================================

print('=' * 70)
print('TMIDIX MIDI Processor')
print('=' * 70)
print('Starting up...')
print('=' * 70)

###########

melody_chords_f = []
melody_chords_f_aug = []

files_count = 0

print('Processing MIDI files. Please wait...')
print('=' * 70)

for i in tqdm(range(0, len(filez), 16)):

    output = Parallel(n_jobs=4, verbose=0)(delayed(TMIDIX_MIDI_Processor)(fa) for fa in filez[i:i+16])

    for o in output:

        if o is not None:
            melody_chords_f.append(o[0])
            melody_chords_f_aug.append(o[1])
            files_count += 1

    # Saving every 2560 processed files
    if files_count % 2560 == 0 and files_count != 0:
        print('SAVING !!!')
        print('=' * 70)
        print('Saving processed files...')
        print('=' * 70)
        print('Data check:', min(melody_chords_f[0]), '===', max(melody_chords_f[0]), '===', len(list(set(melody_chords_f[0]))), '===', len(melody_chords_f[0]))
        print('=' * 70)
        print('Processed so far:', files_count, 'out of', len(filez), '===', files_count / len(filez), 'good files ratio')
        print('=' * 70)
        count = str(files_count)
        TMIDIX.Tegridy_Any_Pickle_File_Writer(melody_chords_f, '/content/drive/MyDrive/LAKH_INTs_'+count)
        TMIDIX.Tegridy_Any_Pickle_File_Writer(melody_chords_f_aug, '/content/drive/MyDrive/LAKH_AUG_INTs_'+count)

        melody_chords_f = []
        melody_chords_f_aug = []

        print('=' * 70)

print('FINAL SAVING !!!')
print('=' * 70)
print('Saving processed files...')
print('=' * 70)
print('Data check:', min(melody_chords_f[0]), '===', max(melody_chords_f[0]), '===', len(list(set(melody_chords_f[0]))), '===', len(melody_chords_f[0]))
print('=' * 70)
print('Processed so far:', files_count, 'out of', len(filez), '===', files_count / len(filez), 'good files ratio')
print('=' * 70)
count = str(files_count)
TMIDIX.Tegridy_Any_Pickle_File_Writer(melody_chords_f, '/content/drive/MyDrive/LAKH_INTs_'+count)
TMIDIX.Tegridy_Any_Pickle_File_Writer(melody_chords_f_aug, '/content/drive/MyDrive/LAKH_AUG_INTs_'+count)
print('=' * 70)

"""# (TEST INTS)"""

#@title Test INTs

train_data1 = random.choice(melody_chords_f + melody_chords_f_aug)
train_data1 = melody_chords_f[0]
print('Sample INTs', train_data1[:15])

out = train_data1

if len(out) != 0:

    song = out
    song_f = []

    time = 0
    dur = 0
    vel = 90
    pitch = 0
    channel = 0

    for ss in song:

        if 0 <= ss < 512:

            time += ss * 8

        if 512 <= ss < 4608:

            dur = ((ss-512) // 8) * 8
            vel = (((ss-512) % 8)+1) * 15

        if 4608 <= ss < 6784:

            patch = (ss-4608) // 128

            if patch == 16:
              channel = 9
            else:
              if 9 <= patch <= 14:
                channel = patch + 1
              else:
                channel = patch

              if patch == 15:
                channel = 15

            pitch = (ss-4608) % 128

            if patch == 17:
              break

            song_f.append(['note', time, dur, channel, pitch, vel ])

detailed_stats = TMIDIX.Tegridy_ms_SONG_to_MIDI_Converter(song_f,
                                                          output_signature = 'Experimental Music Transformer',
                                                          output_file_name = '/content/Experimental-Music-Trnasformer-Composition',
                                                          track_name='Project Los Angeles',
                                                          list_of_MIDI_patches=[0, 10, 19, 24, 35, 40, 53, 56, 65, 9, 73, 87, 89, 99, 105, 117]
                                                          )

print('Done!')

"""# Congrats! You did it! :)"""