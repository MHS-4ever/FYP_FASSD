from pydub import AudioSegment
import os

def convert_all_to_wav(input_folder, output_folder):
    os.makedirs(output_folder, exist_ok=True)
    files = os.listdir(input_folder)
    total = len(files)
    count = 0

    for filename in files:
        file_path = os.path.join(input_folder, filename)

        # Only process files that are audio files (you can extend this list)
        if filename.lower().endswith(('.mp3', '.flac', '.ogg', '.wav', '.m4a', '.aac')):
            try:
                audio = AudioSegment.from_file(file_path)
                audio = audio.set_frame_rate(16000).set_channels(1)  # 16kHz, mono

                # Prepare output filename with .wav extension
                output_filename = os.path.splitext(filename)[0] + '.wav'
                output_path = os.path.join(output_folder, output_filename)

                audio.export(output_path, format='wav')
                count += 1
                print(f"[{count}/{total}] Converted: {filename} → {output_filename}")

            except Exception as e:
                print(f"Failed to convert {filename}: {e}")

        else:
            print(f"Skipped (not audio): {filename}")

if __name__ == "__main__":
    input_folder = input("Enter the path to the folder containing audio clips: ").strip()
    output_folder = input("Enter the path to the output folder for WAV clips: ").strip()

    convert_all_to_wav(input_folder, output_folder)
