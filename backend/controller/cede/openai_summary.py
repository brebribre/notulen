from __future__ import annotations
import json, math, textwrap, logging
from typing import List, Dict, Optional
from pydantic import BaseModel, Field, ValidationError
from openai import OpenAI
import tiktoken
from dotenv import load_dotenv
import os

logger = logging.getLogger(__name__)

# ---------- 2.1  Pydantic model that mirrors the JSON schema ----------
class MeetingSummary(BaseModel):
    summary: str = Field(..., description="Concise narrative summary (≤150 words)")
    action_items: List[str] = Field(
        default_factory=list,
        description="Bullet list of concrete next steps"
    )
    participants: List[str] = Field(
        default_factory=list,
        description="Names or email handles of meeting attendees"
    )

SCHEMA = {
    "name": "meeting_summary",
    "schema": MeetingSummary.model_json_schema(),
    "strict": True
}

# ---------- 2.2  Core utility ----------
class TranscriptSummarizer:
    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "gpt-4o",
        max_tokens: int = 4096,
        chunk_overlap_chars: int = 200,
    ):
        if not api_key:
            load_dotenv()
            api_key = os.getenv('OPENAI_API_KEY')
        if not api_key:
            raise ValueError("OpenAI API key is required. Set OPENAI_API_KEY environment variable or pass directly.")
        
        self.client = OpenAI(api_key=api_key)
        self.model = model
        self.max_tokens = max_tokens
        self.encoder = tiktoken.encoding_for_model(model)
        self.chunk_overlap_chars = chunk_overlap_chars

    # ---- helper that measures prompt size in tokens ----
    def _num_tokens(self, text: str) -> int:
        return len(self.encoder.encode(text))

    # ---- chunk transcript if necessary ----
    def _chunk(self, transcript: str, target_tokens: int = 3500) -> List[str]:
        """Return a list of transcript chunks that each fit within target_tokens."""
        words = transcript.split()
        current, chunks = [], []
        for w in words:
            current.append(w)
            if self._num_tokens(" ".join(current)) > target_tokens:
                # backtrack until we’re under the limit
                while self._num_tokens(" ".join(current)) > target_tokens:
                    current.pop()
                chunks.append(" ".join(current))
                current = words[max(0, len(chunks) * target_tokens // 4):]  # overlap
        if current:
            chunks.append(" ".join(current))
        return chunks

    # ---- single call that forces JSON output ----
    def _call_structured(self, prompt: str) -> dict:
        completion = self.client.beta.chat.completions.parse(
            model=self.model,
            messages=[{"role": "system",
                    "content": "You are a world-class meetings assistant."
                     "Create a concise summary of the meeting, including action items and participants."},
                    {"role": "user", "content": prompt}],
            response_format=MeetingSummary
        )

        result: MeetingSummary = completion.choices[0].message
        if (result.refusal):
            #print(result.refusal)
            return result.refusal
        else:
            #print(result.parsed)
            return result.parsed 

    # ---- public API ---------------------------------------------------
    def summarize(self, transcript: str) -> MeetingSummary:
        try:
            if self._num_tokens(transcript) < self.max_tokens - 500:
                result = self._call_structured(transcript)
            else:
                partials = [self._call_structured(chunk) for chunk in self._chunk(transcript)]
                combined = "\n\n".join(p.summary for p in partials)
                result = self._call_structured(
                    f"These are partial summaries:\n{combined}\n\n"
                    "Merge them into one cohesive summary, "
                    "deduplicating action_items and participants."
                )
            print(result)
            return result
        except (ValidationError, json.JSONDecodeError) as e:
            logger.error("Parsing failed: %s", e)
            raise
