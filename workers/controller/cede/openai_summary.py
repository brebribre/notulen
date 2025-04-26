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
    def _chunk(self, transcript: str, target_tokens: int = 3500) -> list[str]:
        """Fast O(n) tokenizer-first chunker with overlap."""
        tokens = self.encoder.encode(transcript)                    # ① one token pass
        step   = target_tokens - self.chunk_overlap_chars
        slices = (tokens[i : i + target_tokens]                     # ② slice tokens
                for i in range(0, len(tokens), step))
        chunks = [self.encoder.decode(s) for s in slices]           # ③ decode back
        return chunks

