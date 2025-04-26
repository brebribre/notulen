import os
import json
from typing import Optional
from openai import OpenAI
from dotenv import load_dotenv

class Qna:
    """Utility class for OpenAI API interactions"""

    def __init__(self, api_key: Optional[str] = None):
        if not api_key:
            load_dotenv()
            api_key = os.getenv('OPENAI_API_KEY')

        if not api_key:
            raise ValueError("OpenAI API key is required. Set OPENAI_API_KEY environment variable or pass directly.")

        self.client = OpenAI(api_key=api_key)

    def ask_question_with_transcript(self, transcript_file: str, question: str) -> str:
        """
        Send a prompt to OpenAI API by reading transcript and question from text files.

        Args:
            transcript_file (str): Path to the transcript text file.
            question_file (str): Path to the question text file.

        Returns:
            str: The model's response.
        """
        with open(transcript_file, 'r', encoding='utf-8') as tf:
            transcript = tf.read()

        prompt = (
            f"You are given the following transcript:\n\n{transcript}\n\n"
            f"Based on the transcript, answer the following question:\n{question}"
        )

        response = self.client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.5,
            max_tokens=500
        )

        return response.choices[0].message.content.strip()

# Example usage:
#q = Querying()
#response = q.ask_question_with_transcript("transcript.txt", "question.txt")
#print(response)