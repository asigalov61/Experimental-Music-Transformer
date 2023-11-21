# -*- coding: utf-8 -*-
"""Experimental_Music_Transformer_Version_1.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1k0wDK63L6iJCBKwaUGLqbvCYGsP8cpOo

# Experimental Music Transformer Version 1 (ver. 0.5)

***

Powered by tegridy-tools: https://github.com/asigalov61/tegridy-tools

***

WARNING: This complete implementation is a functioning model of the Artificial Intelligence. Please excercise great humility, care, and respect. https://www.nscai.gov/

***

#### Project Los Angeles

#### Tegridy Code 2023

***

# (GPU CHECK)
"""

#@title NVIDIA GPU check
!nvidia-smi

"""# (SETUP ENVIRONMENT)"""

#@title Install dependencies
!git clone --depth 1 https://github.com/asigalov61/Experimental-Music-Transformer
!pip install huggingface_hub
!pip install torch
!pip install einops
!pip install torch-summary
!pip install tqdm
!pip install matplotlib
!apt install fluidsynth #Pip does not work for some reason. Only apt works

# Commented out IPython magic to ensure Python compatibility.
#@title Import modules

print('=' * 70)
print('Loading core Experimental Music Transformer modules...')

import os
import copy
import pickle
import secrets
import statistics
from time import time
import tqdm

print('=' * 70)
print('Loading main Experimental Music Transformer modules...')
import torch

# %cd /content/Experimental-Music-Transformer

import TMIDIX

from midi_to_colab_audio import midi_to_colab_audio

from x_transformer_1_23_2 import *

import random

# %cd /content/
print('=' * 70)
print('Loading aux Experimental Music Transformer modules...')

import matplotlib.pyplot as plt

from torchsummary import summary
from sklearn import metrics

from IPython.display import Audio, display

from huggingface_hub import hf_hub_download

from google.colab import files

print('=' * 70)
print('Done!')
print('Enjoy! :)')
print('=' * 70)

"""# (LOAD MODEL)"""

#@title Load Experimental Music Transformer Large Model

#@markdown Very fast model, 32 layers, 245k MIDIs training corpus

full_path_to_model_checkpoint = "/content/Experimental-Music-Transformer/Models/Version-1/Experimental_Music_Transformer_Version_1_Large_Trained_Model_18581_steps_0.636_loss_0.823_acc.pth" #@param {type:"string"}

#@markdown Model precision option

model_precision = "bfloat16" # @param ["bfloat16", "float16"]

#@markdown bfloat16 == Half precision/faster speed (if supported, otherwise the model will default to float16)

#@markdown float16 == Full precision/fast speed

plot_tokens_embeddings = False # @param {type:"boolean"}

print('=' * 70)
print('Loading Experimental Music Transformer Large Pre-Trained Model...')
print('Please wait...')
print('=' * 70)

if os.path.isfile(full_path_to_model_checkpoint):
  print('Model already exists...')

else:
  hf_hub_download(repo_id='asigalov61/Experimental-Music-Transformer',
                  filename='Experimental_Music_Transformer_Version_1_Large_Trained_Model_18581_steps_0.636_loss_0.823_acc.pth',
                  local_dir='/content/Experimental-Music-Transformer/Models/Version-1',
                  local_dir_use_symlinks=False)

print('=' * 70)
print('Instantiating model...')

torch.backends.cuda.matmul.allow_tf32 = True # allow tf32 on matmul
torch.backends.cudnn.allow_tf32 = True # allow tf32 on cudnn
device_type = 'cuda'

if model_precision == 'bfloat16' and torch.cuda.is_bf16_supported():
  dtype = 'bfloat16'
else:
  dtype = 'float16'

if model_precision == 'float16':
  dtype = 'float16'

ptdtype = {'float32': torch.float32, 'bfloat16': torch.bfloat16, 'float16': torch.float16}[dtype]
ctx = torch.amp.autocast(device_type=device_type, dtype=ptdtype)

SEQ_LEN = 8192

# instantiate the model

model = TransformerWrapper(
    num_tokens = 7578,
    max_seq_len = SEQ_LEN,
    attn_layers = Decoder(dim = 1024, depth = 32, heads = 32, attn_flash = True)
)

model = AutoregressiveWrapper(model, ignore_index=7577)

model.cuda()
print('=' * 70)

print('Loading model checkpoint...')

model.load_state_dict(torch.load(full_path_to_model_checkpoint))
print('=' * 70)

model.eval()

print('Done!')
print('=' * 70)

print('Model will use', dtype, 'precision...')
print('=' * 70)

# Model stats
print('Model summary...')
summary(model)

# Plot Token Embeddings
if plot_tokens_embeddings:
  tok_emb = model.net.token_emb.emb.weight.detach().cpu().tolist()

  cos_sim = metrics.pairwise_distances(
    tok_emb, metric='cosine'
  )
  plt.figure(figsize=(7, 7))
  plt.imshow(cos_sim, cmap="inferno", interpolation="nearest")
  im_ratio = cos_sim.shape[0] / cos_sim.shape[1]
  plt.colorbar(fraction=0.046 * im_ratio, pad=0.04)
  plt.xlabel("Position")
  plt.ylabel("Position")
  plt.tight_layout()
  plt.plot()
  plt.savefig("/content/Experimental-Music-Transformer-Large-Tokens-Embeddings-Plot.png", bbox_inches="tight")

"""# (GENERATE)

# (IMPROV)
"""

#@title Standard Improv Generator

#@markdown Improv type

improv_type = "Random Freestyle" # @param ["Random Freestyle", "Freestyle without Drums", "Freestyle with Drums", "Custom"]

#@markdown Custom Improv settings

first_note_MIDI_patch_number = 0 # @param {type:"slider", min:0, max:128, step:1}
first_note_MIDI_pitch_number = 60 # @param {type:"slider", min:1, max:127, step:1}
add_drums = False #@param {type:"boolean"}

#@markdown Generation settings

number_of_tokens_tp_generate = 1010 # @param {type:"slider", min:30, max:8190, step:4}
number_of_batches_to_generate = 4 #@param {type:"slider", min:1, max:16, step:1}
temperature = 0.9 # @param {type:"slider", min:0.1, max:1, step:0.05}

#@markdown Other settings

render_MIDI_to_audio = True # @param {type:"boolean"}

print('=' * 70)
print('Experimental Music Transformer Standard Improv Model Generator')
print('=' * 70)

if improv_type == 'Random Freestyle':

  outy = [7575]

if improv_type == 'Freestyle without Drums':

  outy = [7575, 7428]

if improv_type == 'Freestyle with Drums':

  outy = [7575, 7429]

if improv_type == 'Custom':

  if add_drums:
    drumsp = 7429 # Yes
  else:
    drumsp = 7428 # No

  outy = [7575,
          drumsp,
          7430+first_note_MIDI_patch_number,
          7447+first_note_MIDI_pitch_number]

print('Selected Improv sequence:')
print(outy)
print('=' * 70)

inp = [outy] * number_of_batches_to_generate

inp = torch.LongTensor(inp).cuda()

with ctx:
  out = model.generate(inp,
                        number_of_tokens_tp_generate,
                        temperature=temperature,
                        return_prime=True,
                        verbose=True)

out0 = out.tolist()

print('=' * 70)
print('Done!')
print('=' * 70)

#======================================================================

print('Rendering results...')

for i in range(number_of_batches_to_generate):

  print('=' * 70)
  print('Batch #', i)
  print('=' * 70)

  out1 = out0[i]

  print('Sample INTs', out1[:12])
  print('=' * 70)

  if len(out1) != 0:

      song = out1
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

              if emph == 1:
                  song_f.append(['text_event', time, 'Emph'])

              song_f.append(['note', time, dur, channel, pitch, vel ])

          if 6784 < ss < 6787:
              emph = ss - 6784

              if emph == 1:
                song_f.append(['text_event', time, 'Emph'])


      data = TMIDIX.Tegridy_ms_SONG_to_MIDI_Converter(song_f,
                                                      output_signature = 'Experimental Music Transformer',
                                                      output_file_name = '/content/Experimental-Music-Transformer-Composition_'+str(i),
                                                      track_name='Project Los Angeles',
                                                      list_of_MIDI_patches=[0, 10, 19, 24, 35, 40, 53, 56, 65, 9, 73, 87, 89, 99, 105, 117]
                                                      )


      print('=' * 70)
      print('Displaying resulting composition...')
      print('=' * 70)

      fname = '/content/Experimental-Music-Transformer-Composition_'+str(i)

      x = []
      y =[]
      c = []

      colors = ['red', 'yellow', 'green', 'cyan',
                'blue', 'pink', 'orange', 'purple',
                'gray', 'white', 'gold', 'silver',
                'lightgreen', 'indigo', 'maroon', 'turquoise']

      for s in song_f:
        if s[0] == 'note':
          x.append(s[1] / 1000)
          y.append(s[4])
          c.append(colors[s[3]])

      if render_MIDI_to_audio:
        midi_audio = midi_to_colab_audio(fname + '.mid')
        display(Audio(midi_audio, rate=16000, normalize=False))

      plt.figure(figsize=(14,5))
      ax=plt.axes(title=fname)
      ax.set_facecolor('black')

      plt.scatter(x,y, c=c)
      plt.xlabel("Time")
      plt.ylabel("Pitch")
      plt.show()

"""# (CUSTOM MIDI)"""

#@title Load Seed MIDI

#@markdown Press play button to to upload your own seed MIDI or to load one of the provided sample seed MIDIs from the dropdown list below

select_seed_MIDI = "Nothing Else Matters" # @param ["Upload your own custom MIDI", "Nothing Else Matters", "Sharing The Night Together", "Honesty", "House Of The Rising Sun"]
render_MIDI_to_audio = False # @param {type:"boolean"}

print('=' * 70)
print('Experimental Music Transformer Seed MIDI Loader')
print('=' * 70)

f = ''

if select_seed_MIDI != "Upload your own custom MIDI":
  print('Loading seed MIDI...')
  f = '/content/Experimental-Music-Transformer/Seeds/'+select_seed_MIDI+'.mid'
  score = TMIDIX.midi2single_track_ms_score(open(f, 'rb').read(), recalculate_channels=False, pass_old_timings_events=True)

else:
  print('Upload your own custom MIDI...')
  print('=' * 70)
  uploaded_MIDI = files.upload()
  if list(uploaded_MIDI.keys()):
    f = list(uploaded_MIDI.keys())[0]
    score = TMIDIX.midi2single_track_ms_score(open(f, 'rb').read(), recalculate_channels=False, pass_old_timings_events=True)

if f != '':

  print('=' * 70)
  print('File:', f)
  print('=' * 70)

  #=======================================================
  # START PROCESSING

  score = TMIDIX.midi2single_track_ms_score(open(f, 'rb').read(), recalculate_channels=False, pass_old_timings_events=True)

  # INSTRUMENTS CONVERSION CYCLE
  events_matrix = []
  itrack = 1
  patches = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]

  emph_once = False
  emphasis_time = 0

  tpq = 0
  tempo = 0
  time_sig = 0
  key_sig = 0

  while itrack < len(score):
      for event in score[itrack]:

          if event[0] != 'note':
            event.extend([0, 128])
          else:
            event.extend([0, 0])

          if event[0] == 'text_event' or event[0] == 'lyric' or event[0] == 'patch_change' or event[0] == 'time_signature':
            event[4] = 128

          events_matrix.append(event)

      itrack += 1

  events_matrix.sort(key=lambda x: x[4], reverse = True)
  events_matrix.sort(key=lambda x: x[1])

  events_matrix1 = []

  pt = events_matrix[0][1]

  for event in events_matrix:
          if event[0] == 'patch_change':
                patches[event[2]] = event[3]

          #========================================================================
          # Emphasis

          if event[0] == 'text_event' or event[0] == 'lyric':
                emphasis_time = event[1]
                emph_once = True

          if event[0] == 'note' and int(event[1] / 8) > int(emphasis_time / 8) and event[1] > pt:
                event[7] = 2
                emph_once = False

          if event[0] == 'note' and int(event[1] / 8) == int(emphasis_time / 8) and emph_once:
                event[7] = 1
                emph_once = False

          pt = event[1]

          #========================================================================
          # Notes

          if event[0] == 'note':
                event[6] = patches[event[3]]

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

                #=======================================================
                # MAIN PROCESSING
                #=======================================================

                #=======================================================
                # Timings
                #=======================================================

                events_matrix2 = []

                # Recalculating timings
                for e in events_matrix1:

                    # Original timings
                    e[1] = int(e[1] / 8)
                    e[2] = int(e[2] / 8)

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
                melody_chords1 = []

                # Break between compositions / Intro seq

                if 9 in instruments_list:
                    drums_present = 7429 # Yes
                else:
                    drums_present = 7428 # No

                if events_matrix1[0][3] != 9:
                    pat = events_matrix1[0][6] // 8
                else:
                    pat = 16

                ptc = events_matrix1[0][4]

                melody_chords.extend([7575, drums_present, 7430+pat, 7447+ptc]) # Intro seq
                melody_chords1.append([7575, drums_present, 7430+pat, 7447+ptc])
                #=======================================================
                # PROCESSING CYCLE
                #=======================================================

                pe = events_matrix1[0]

                for e in events_matrix1:

                    #=======================================================
                    # Timings...

                    # Cliping all values...
                    delta_time = max(0, min(511, e[1]-pe[1]))

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
                    # FINAL NOTE SEQ

                    # Writing final note asynchronously

                    dur_vel = (8 * dur) + velocity
                    pat_ptc = (128 * pat) + ptc

                    melody_chords.extend([emph+6784, delta_time, dur_vel+512, pat_ptc+4608])
                    melody_chords1.append([emph+6784, delta_time, dur_vel+512, pat_ptc+4608])

                    pe = e

                #=======================================================

                emphasis = [m for m in melody_chords if 6784 <= m <= 6785]

  #=======================================================

  song = melody_chords

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

          if emph == 1:
            song_f.append(['text_event', time, 'Emph'])

          song_f.append(['note', time, dur, channel, pitch, vel ])

      if 6784 < ss < 6787:
          emph = ss - 6784

  data = TMIDIX.Tegridy_ms_SONG_to_MIDI_Converter(song_f,
                                                  output_signature = 'Experimental Music Transformer',
                                                  output_file_name = '/content/Experimental-Music-Transformer-Seed-Composition',
                                                  track_name='Project Los Angeles',
                                                  list_of_MIDI_patches=[0, 10, 19, 24, 35, 40, 53, 56, 65, 9, 73, 87, 89, 99, 105, 117]
                                                  )

  #=======================================================

  print('=' * 70)
  print('Composition stats:')
  print('Composition has', len(melody_chords1), 'notes')
  print('Composition has', len(melody_chords), 'tokens')
  print('=' * 70)

  print('Displaying resulting composition...')
  print('=' * 70)

  fname = '/content/Experimental-Music-Transformer-Seed-Composition'

  x = []
  y =[]
  c = []

  colors = ['red', 'yellow', 'green', 'cyan',
            'blue', 'pink', 'orange', 'purple',
            'gray', 'white', 'gold', 'silver',
            'lightgreen', 'indigo', 'maroon', 'turquoise']

  for s in song_f:
    if s[0] == 'note':
      x.append(s[1] / 1000)
      y.append(s[4])
      c.append(colors[s[3]])

  if render_MIDI_to_audio:
    midi_audio = midi_to_colab_audio(fname + '.mid')
    display(Audio(midi_audio, rate=16000, normalize=False))

  plt.figure(figsize=(14,5))
  ax=plt.axes(title=fname)
  ax.set_facecolor('black')

  plt.scatter(x,y, c=c)
  plt.xlabel("Time")
  plt.ylabel("Pitch")
  plt.show()

else:
  print('=' * 70)

"""# (CONTINUATION)"""

#@title Standard Continuation

#@markdown Generation settings

try_to_generate_outro = False #@param {type:"boolean"}
number_of_prime_tokens = 1008 # @param {type:"slider", min:4, max:8190, step:4}
number_of_tokens_to_generate = 1026 # @param {type:"slider", min:30, max:8190, step:4}
number_of_batches_to_generate = 4 #@param {type:"slider", min:1, max:16, step:1}
temperature = 0.9 # @param {type:"slider", min:0.1, max:1, step:0.05}

#@markdown Other settings
include_prime_tokens_in_generated_output = True #@param {type:"boolean"}
allow_model_to_stop_generation_if_needed = False #@param {type:"boolean"}
render_MIDI_to_audio = True # @param {type:"boolean"}

print('=' * 70)
print('Experimental Music Transformer Standard Continuation Model Generator')
print('=' * 70)

if allow_model_to_stop_generation_if_needed:
  min_stop_token = 7576
else:
  min_stop_token = None

outy = melody_chords[:number_of_prime_tokens]

if try_to_generate_outro:
  outy.extend([6787, 6787])

inp = [outy] * number_of_batches_to_generate

inp = torch.LongTensor(inp).cuda()

with ctx:
  out = model.generate(inp,
                        number_of_tokens_to_generate,
                        temperature=temperature,
                        return_prime=include_prime_tokens_in_generated_output,
                        eos_token=min_stop_token,
                        verbose=True)

out0 = out.tolist()

print('=' * 70)
print('Done!')
print('=' * 70)

#======================================================================
print('Rendering results...')

for i in range(number_of_batches_to_generate):

  print('=' * 70)
  print('Batch #', i)
  print('=' * 70)

  out1 = out0[i]

  print('Sample INTs', out1[:12])
  print('=' * 70)

  if len(out) != 0:

      song = out1
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

              if emph == 1:
                song_f.append(['text_event', time, 'Emph'])

              song_f.append(['note', time, dur, channel, pitch, vel ])

          if 6784 < ss < 6787:
              emph = ss - 6784

      data = TMIDIX.Tegridy_ms_SONG_to_MIDI_Converter(song_f,
                                                      output_signature = 'Experimental Music Transformer',
                                                      output_file_name = '/content/Experimental-Music-Transformer-Composition_'+str(i),
                                                      track_name='Project Los Angeles',
                                                      list_of_MIDI_patches=[0, 10, 19, 24, 35, 40, 53, 56, 65, 9, 73, 87, 89, 99, 105, 117]
                                                      )


      print('=' * 70)
      print('Displaying resulting composition...')
      print('=' * 70)

      fname = '/content/Experimental-Music-Transformer-Composition_'+str(i)

      x = []
      y =[]
      c = []

      colors = ['red', 'yellow', 'green', 'cyan',
                'blue', 'pink', 'orange', 'purple',
                'gray', 'white', 'gold', 'silver',
                'lightgreen', 'indigo', 'maroon', 'turquoise']

      for s in song_f:
        if s[0] == 'note':
          x.append(s[1] / 1000)
          y.append(s[4])
          c.append(colors[s[3]])

      if render_MIDI_to_audio:
        midi_audio = midi_to_colab_audio(fname + '.mid')
        display(Audio(midi_audio, rate=16000, normalize=False))

      plt.figure(figsize=(14,5))
      ax=plt.axes(title=fname)
      ax.set_facecolor('black')

      plt.scatter(x,y, c=c)
      plt.xlabel("Time")
      plt.ylabel("Pitch")
      plt.show()

"""# (INPAINTING)"""

#@title Emphasis-based Notes Inpainting

#@markdown You can stop the inpainting at any time to render partial results

#@markdown Inpainting settings

#@markdown Select MIDI patch present in the composition to inpaint

inpainting_type = "Times-Durations-Velocities-Pitches" # @param ["Pitches", "Durations-Velocities-Pitches", "Times-Durations-Velocities-Pitches"]

#@markdown Generation settings

number_of_prime_notes = 1 # @param {type:"slider", min:1, max:2047, step:1}
number_of_memory_tokens = 8188 # @param {type:"slider", min:4, max:8188, step:4}
number_of_samples_per_inpainted_note = 4 #@param {type:"slider", min:1, max:16, step:1}
temperature = 0.9 # @param {type:"slider", min:0.1, max:1, step:0.05}

#@markdown Other settings

render_MIDI_to_audio = False # @param {type:"boolean"}

print('=' * 70)
print('Experimental Music Transformer Inpainting Model Generator')
print('=' * 70)

if inpainting_type == 'Pitches':
  t1 = 3
  t2 = 1

if inpainting_type == 'Durations-Velocities-Pitches':
  t1 = t2 = 2

if inpainting_type == 'Times-Durations-Velocities-Pitches':
  t1 = 1
  t2 = 3

out2 = []

number_of_prime_tokens = number_of_prime_notes * 4

for m in melody_chords[:number_of_prime_tokens]:
  out2.append(m)

for i in tqdm.tqdm(range(number_of_prime_tokens, len(melody_chords), 4)):

  try:
        out2.extend(melody_chords[i:i+t1])

        if melody_chords[i] < 6787:

          samples = []

          for j in range(number_of_samples_per_inpainted_note):

            inp = torch.LongTensor(out2[-number_of_memory_tokens:]).cuda()

            with ctx:
              out1 = model.generate(inp,
                                    t2,
                                    temperature=temperature,
                                    return_prime=False,
                                    verbose=False)

              with torch.no_grad():
                test_loss, test_acc = model(out1)

            samples.append([out1.tolist()[0], test_acc.tolist()])

          accs = [y[1] for y in samples]
          max_acc = max(accs)
          max_acc_sample = samples[accs.index(max_acc)][0]

          out2.extend(max_acc_sample)

        else:
          out2.extend(melody_chords[i+t1:i+4])

  except KeyboardInterrupt:
    print('Stopping inpainting...')
    break

  except Exception as e:
    print('Error', e)
    break

print('Done!')
print('=' * 70)

#==================================================

print('Rendering results...')
print('=' * 70)

if len(out2) != 0:

    song = out2
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

            if emph == 1:
                song_f.append(['text_event', time, 'Emph'])

            song_f.append(['note', time, dur, channel, pitch, vel ])

        if 6784 < ss < 6787:
            emph = ss - 6784

    data = TMIDIX.Tegridy_ms_SONG_to_MIDI_Converter(song_f,
                                                    output_signature = 'Experimental Music Transformer',
                                                    output_file_name = '/content/Experimental-Music-Transformer-Composition',
                                                    track_name='Project Los Angeles',
                                                    list_of_MIDI_patches=[0, 10, 19, 24, 35, 40, 53, 56, 65, 9, 73, 87, 89, 99, 105, 117]
                                                    )


    print('=' * 70)
    print('Displaying resulting composition...')
    print('=' * 70)

    fname = '/content/Experimental-Music-Transformer-Composition'

    x = []
    y =[]
    c = []

    colors = ['red', 'yellow', 'green', 'cyan',
              'blue', 'pink', 'orange', 'purple',
              'gray', 'white', 'gold', 'silver',
              'lightgreen', 'indigo', 'maroon', 'turquoise']

    for s in song_f:
      if s[0] == 'note':
        x.append(s[1] / 1000)
        y.append(s[4])
        c.append(colors[s[3]])

    if render_MIDI_to_audio:
      midi_audio = midi_to_colab_audio(fname + '.mid')
      display(Audio(midi_audio, rate=16000, normalize=False))

    plt.figure(figsize=(14,5))
    ax=plt.axes(title=fname)
    ax.set_facecolor('black')

    plt.scatter(x,y, c=c)
    plt.xlabel("Time")
    plt.ylabel("Pitch")
    plt.show()

"""# Congrats! You did it! :)"""