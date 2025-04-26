import asyncio
from typing import List
from openai import AsyncOpenAI
from controller.cede.openai_summary import TranscriptSummarizer, MeetingSummary

class AsyncTranscriptSummarizer(TranscriptSummarizer):
    def __init__(self, *args, concurrency: int = 5, **kwargs):
        super().__init__(*args, **kwargs)
        self.client = AsyncOpenAI(api_key=self.client.api_key)   # swap client
        self.semaphore = asyncio.Semaphore(concurrency)          # throttle RPM

    async def _call_structured_async(self, prompt: str) -> MeetingSummary:
        async with self.semaphore:
            completion = await self.client.beta.chat.completions.parse(
                model=self.model,
                messages=[{"role": "system",
                        "content": "You are a world-class meetings assistant."
                        "Create a detailed summary of the meeting, including action items and participants. Never hallucinate your data. if the transcript is not long enough, just return an empty summary or participants. Never miss any factual information. If you detect a participant, always use the full name if possible. If there are multiple topics to cover, make sure to always include all the topics in the summary. Return your output in markdown format."},
                        {"role": "user", "content": prompt}],
                response_format=MeetingSummary,
                temperature=0.0
        )

        result: MeetingSummary = completion.choices[0].message
        if getattr(result, "refusal", None):                # spec per helpers.md :contentReference[oaicite:1]{index=1}
            raise RuntimeError(f"Model refused: {result.refusal}")
        return result.parsed 

    async def summarize_async(self, transcript: str) -> MeetingSummary:
        if self._num_tokens(transcript) < self.max_tokens - 500:
            return await self._call_structured_async(transcript)

        # --- map step ---------------------------------------------------
        chunks: List[str] = self._chunk(transcript)
        tasks  = [self._call_structured_async(c) for c in chunks]
        partials: list[MeetingSummary] = await asyncio.gather(*tasks)

        # --- reduce step (still async) ----------------------------------
        combined = "\n\n".join(p.summary for p in partials)  # dot-notation, not dict
        result = await self._call_structured_async(
            f"These are partial summaries:\n{combined}\n\n"
            "Merge them into one cohesive summary, "
            "deduplicating action_items and participants."
        )
        print(result)
        return result
