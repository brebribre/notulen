import os
from speech_to_text import SpeechToText

# Ensure the OpenAI API key is set
api_key = os.getenv("OPENAI_API_KEY")

# Initialize the SpeechToText instance
transcriber = SpeechToText(api_key=api_key)

audio_paths= [
    "sample_speech.mp3",
    "sample_meeting.mp3",
    "sample_meeting2.mp4"
]

# Select the audio file to transcribe
audio_path = audio_paths[2]

# Sample usage of the SpeechToText class
# Transcribe the audio file by path
full_transcription = transcriber.speech_to_text(audio_path)
print(full_transcription)