import os
from speech_to_text import SpeechToText

# Ensure the OpenAI API key is set
api_key = os.getenv("OPENAI_API_KEY")
# if not api_key:
#     raise ValueError("OPENAI_API_KEY environment variable is not set.")

# Initialize the SpeechToText instance
transcriber = SpeechToText(api_key=api_key)

audio_paths= [
    "sample_speech.mp3",
    "sample_meeting.mp3",
    "sample_meeting2.mp4"
]

audio_path = audio_paths[1]

# Open the audio file and transcribe
with open(audio_path, "rb") as audio_file:
    full_transcription = transcriber.speech_to_text(audio_file)
    print(full_transcription)