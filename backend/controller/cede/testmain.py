import asyncio, os
from openai_summary_async import AsyncTranscriptSummarizer

async def main():
    ts = AsyncTranscriptSummarizer(concurrency=8)   # tune to your tier
    with open("transcript2.txt") as f:
        summary = await ts.summarize_async(f.read())
    print(summary.model_dump_json(indent=2))

asyncio.run(main())
