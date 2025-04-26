import io
import soundfile as sf
from dotenv import load_dotenv
from concurrent.futures import ThreadPoolExecutor
from typing import Optional
import os
from openai import OpenAI
from pydub import AudioSegment
from pydub.utils import which
from pydub import utils as pydub_utils
import pydub

class SpeechToText:
    def __init__(self, api_key: Optional[str] = None):
        if not api_key:
            load_dotenv()
            api_key = os.getenv('OPENAI_API_KEY')
        if not api_key:
            raise ValueError("OpenAI API key is required.")
        self.client = OpenAI(api_key=api_key)

    def speech_to_text(self, audio_path):
        ffmpeg_path = os.path.join(os.path.dirname(__file__), "ffmpeg")
        ffprobe_path = os.path.join(os.path.dirname(__file__), "ffprobe")

        AudioSegment.converter = ffmpeg_path
        AudioSegment.ffprobe = ffprobe_path
        pydub.AudioSegment.converter = ffmpeg_path
        pydub.AudioSegment.ffprobe = ffprobe_path
        pydub.utils.get_prober_name = lambda: ffprobe_path

        original_which = pydub_utils.which

        def custom_which(program):
            if program == "ffmpeg":
                return ffmpeg_path
            if program == "ffprobe":
                return ffprobe_path
            return original_which(program)

        pydub_utils.which = custom_which
        
        if not (os.path.isfile(ffmpeg_path) and os.access(ffmpeg_path, os.X_OK)):
            raise FileNotFoundError(f"FFmpeg binary not found or not executable at {ffmpeg_path}. Please ensure it exists and is executable.")

        if not (os.path.isfile(ffprobe_path) and os.access(ffprobe_path, os.X_OK)):
            raise FileNotFoundError(f"FFprobe binary not found or not executable at {ffprobe_path}. Please ensure it exists and is executable.")
        
        audio = AudioSegment.from_file(audio_path)
        
        if len(audio) <= 60000:
            buffer = io.BytesIO()
            audio.export(buffer, format="wav", codec="pcm_s16le")
            buffer.name = "audio.wav"
            buffer.seek(0)
            
            transcription = self.client.audio.transcriptions.create(
                model="gpt-4o-transcribe",
                file=buffer,
                response_format="json"
            )
            return transcription.text
        else:
            chunk_duration_ms = 120 * 1000  # 120 seconds = 2 minutes

            chunks = []
            for i in range(0, len(audio), chunk_duration_ms):
                chunk = audio[i:i + chunk_duration_ms]
                buffer = io.BytesIO()
                chunk.export(buffer, format="wav", codec="pcm_s16le")
                buffer.name = "audio.wav"  # <--- Add this!
                buffer.seek(0)
                chunks.append(buffer)

            print(f"Number of chunks: {len(chunks)}")
            
            def transcribe(chunk_io):
                chunk_io.seek(0)
                transcription = self.client.audio.transcriptions.create(
                    model="gpt-4o-transcribe",
                    file=chunk_io,
                    response_format="json"
                )
                return transcription.text

            results = []
            with ThreadPoolExecutor() as executor:
                futures = [executor.submit(transcribe, chunk) for chunk in chunks]
                for future in futures:
                    results.append(future.result())

            full_text = " ".join(results)
            return full_text