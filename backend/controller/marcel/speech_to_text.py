import io
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
    """
    A class to handle speech-to-text transcription using OpenAI's API.
    
    This class initializes an OpenAI client with the provided API key and
    provides a method to transcribe audio files into text. It supports
    handling long audio files by splitting them into chunks and transcribing
    them in parallel.
    """
    def __init__(self, api_key: Optional[str] = None):
        if not api_key:
            load_dotenv()
            api_key = os.getenv('OPENAI_API_KEY')
        if not api_key:
            raise ValueError("OpenAI API key is required.")
        self.client = OpenAI(api_key=api_key)

    def speech_to_text(self, audio_path: str):
        """
        Transcribe an audio file to text.

        Parameters:
            audio_path (str): The file path to the audio file to be transcribed.

        Returns:
            str: The transcribed text from the audio.
        
        This method sets up the environment for ffmpeg and ffprobe binaries,
        loads the audio file, determines whether the audio length requires
        chunking, and performs transcription either directly or in parallel
        for chunks longer than 60 seconds.
        """
        # Setup paths to ffmpeg and ffprobe binaries relative to this script
        ffmpeg_path = os.path.join(os.path.dirname(__file__), "ffmpeg")
        ffprobe_path = os.path.join(os.path.dirname(__file__), "ffprobe")

        # Configure pydub to use the specified ffmpeg and ffprobe binaries
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
        
        # Verify ffmpeg binary exists and is executable
        if not (os.path.isfile(ffmpeg_path) and os.access(ffmpeg_path, os.X_OK)):
            raise FileNotFoundError(f"FFmpeg binary not found or not executable at {ffmpeg_path}. Please ensure it exists and is executable.")

        # Verify ffprobe binary exists and is executable
        if not (os.path.isfile(ffprobe_path) and os.access(ffprobe_path, os.X_OK)):
            raise FileNotFoundError(f"FFprobe binary not found or not executable at {ffprobe_path}. Please ensure it exists and is executable.")
        
        # Load the audio file into an AudioSegment object
        with open(audio_path, "rb") as audio_file:
            audio_file_bytes = io.BytesIO(audio_file.read())
            audio_file_bytes.name = os.path.basename(audio_path)
            audio_file_bytes.seek(0)
        audio = AudioSegment.from_file(audio_file_bytes)
        
        # If audio length is 60 seconds or less, transcribe directly
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
            # For longer audio, split into 2-minute chunks
            chunk_duration_ms = 120 * 1000  # 120 seconds = 2 minutes

            chunks = []
            for i in range(0, len(audio), chunk_duration_ms):
                chunk = audio[i:i + chunk_duration_ms]
                buffer = io.BytesIO()
                chunk.export(buffer, format="wav", codec="pcm_s16le")
                buffer.name = "audio.wav"
                buffer.seek(0)
                chunks.append(buffer)

            print(f"Number of chunks: {len(chunks)}")
            
            # Function to transcribe a single chunk
            def transcribe(chunk_io):
                chunk_io.seek(0)
                transcription = self.client.audio.transcriptions.create(
                    model="gpt-4o-transcribe",
                    file=chunk_io,
                    response_format="json"
                )
                return transcription.text

            # Transcribe chunks in parallel using ThreadPoolExecutor
            results = []
            with ThreadPoolExecutor() as executor:
                futures = [executor.submit(transcribe, chunk) for chunk in chunks]
                for future in futures:
                    results.append(future.result())

            # Combine all chunk transcriptions into a single string
            full_text = " ".join(results)
            return full_text