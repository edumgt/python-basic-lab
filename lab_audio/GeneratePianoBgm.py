import numpy as np
from scipy.io.wavfile import write
import os
from pydub import AudioSegment

# Constants
sample_rate = 44100
duration = 60
tempo_bpm = 80
beats_per_measure = 4
measure_duration_sec = (60 / tempo_bpm) * beats_per_measure
measures = int(duration / measure_duration_sec)

# Note generator
def generate_note(freq, length_sec, volume=0.4):
    t_note = np.linspace(0, length_sec, int(sample_rate * length_sec), False)
    note = np.sin(freq * 2 * np.pi * t_note) * volume
    envelope = np.linspace(1, 0, note.size)  # fade out
    return note * envelope

# Chord generator (N-finger chords)
def generate_chord(freqs, length_sec, volume=0.4):
    chord = sum(generate_note(f, length_sec, volume) for f in freqs)
    chord /= len(freqs)
    return chord

# Extended frequency dictionary
base_freqs = {
    "C3": 130.81,
    "D3": 146.83,
    "E3": 164.81,
    "F3": 174.61,
    "G3": 196.00,
    "A3": 220.00,
    "B3": 246.94,
    "C4": 261.63,
    "D4": 293.66,
    "E4": 329.63,
    "F4": 349.23,
    "G4": 392.00,
    "A4": 440.00,
    "B4": 493.88,
    "C5": 523.25
}

# 6-finger chord patterns
chord_patterns = [
    ["C3", "E3", "G3", "B3", "D4", "G4"],  # Cmaj9-like
    ["F3", "A3", "C4", "E4", "G4", "C5"],  # Fmaj9
    ["G3", "B3", "D4", "F4", "A4", "D4"],  # G9 or Gm9
    ["A3", "C4", "E4", "G4", "B4", "C5"],  # Am9
    ["D3", "F3", "A3", "C4", "E4", "G4"],  # Dm11
    ["E3", "G3", "B3", "D4", "F4", "A4"]   # Em11
]

melody = np.array([])

# Construct full piece
for i in range(measures):
    pattern_idx = i % len(chord_patterns)
    chord_freqs = [base_freqs[n] for n in chord_patterns[pattern_idx]]
    melody = np.concatenate([melody, generate_chord(chord_freqs, measure_duration_sec)])

# Adjust length
total_samples = int(sample_rate * duration)
if len(melody) < total_samples:
    melody = np.pad(melody, (0, total_samples - len(melody)), 'constant')
else:
    melody = melody[:total_samples]

# Convert to 16-bit PCM
audio = np.int16(melody * 32767)

# Save WAV
wav_filename = 'piano_six_finger_loop.wav'
write(wav_filename, sample_rate, audio)

# Convert to MP3
mp3_filename = 'sleepback.mp3'
sound = AudioSegment.from_wav(wav_filename)
sound.export(mp3_filename, format="mp3")

# Clean up
os.remove(wav_filename)

print(f"✅ 6-finger 화음 기반 60초 루프 mp3 생성 완료: {mp3_filename}")
