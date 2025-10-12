import os
from TTS.api import TTS

# choose a pretrained model
model_name = "tts_models/en/ljspeech/tacotron2-DDC"

# load model
tts = TTS(model_name)

# read words
with open("words.txt", "r") as f:
    words = [line.strip() for line in f.readlines() if line.strip()]

# make output folder
os.makedirs("outputs", exist_ok=True)

# generate audio for each word
for idx, word in enumerate(words, 1):
    out_path = f"outputs/{idx:03d}_{word}.wav"
    print(f"[{idx}/{len(words)}] Generating {word} -> {out_path}")
    tts.tts_to_file(text=word, file_path=out_path)
