import whisper
from gtts import gTTS
import sounddevice as sd
import numpy as np
from scipy.io.wavfile import write
import os
from langdetect import detect, DetectorFactory

# Ensure consistent LangDetect results
DetectorFactory.seed = 0

class VoiceProcessor:
    def __init__(self, model):
        # Pass a preloaded Whisper model
        self.whisper_model = model

    def record_audio(self, duration=5, samplerate=16000):
        print("Recording audio...")
        audio = sd.rec(int(duration * samplerate), samplerate=samplerate, channels=1, dtype="float32")
        sd.wait()
        print("Recording complete.")
        return audio.flatten()

    def transcribe_audio(self, audio, samplerate=16000):
        # Save audio to a temporary WAV file
        temp_audio_path = "temp_audio.wav"
        audio_data = (audio * 32767).astype(np.int16)  # Convert to 16-bit PCM format
        write(temp_audio_path, samplerate, audio_data)  # Use scipy.io.wavfile.write to save the file

        # Transcribe using Whisper
        print("Transcribing audio...")
        result = self.whisper_model.transcribe(temp_audio_path)
        os.remove(temp_audio_path)  # Cleanup temp file
        return result["text"], result["language"]

    def detect_language(self, text, whisper_language):
        # Validate Whisper's detected language with LangDetect
        detected_text_language = detect(text)
        print(f"Whisper Detected Language: {whisper_language}")
        print(f"LangDetect Detected Language: {detected_text_language}")

        # Use LangDetect for a second opinion if required
        if whisper_language == detected_text_language:
            return whisper_language
        else:
            print("Language conflict detected. Defaulting to Whisper result.")
            return whisper_language

    def synthesize_speech(self, text, lang="en", output_path="response.mp3"):
        # Use gTTS to convert text to speech
        tts = gTTS(text=text, lang=lang)
        tts.save(output_path)
        print(f"Response audio saved to {output_path}.")
        return output_path
