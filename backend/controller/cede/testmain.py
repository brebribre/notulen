from openai_summary import TranscriptSummarizer
ts = TranscriptSummarizer()
with open("transcript2.txt") as f:
    print(ts.summarize(f.read()).model_dump_json(indent=2))
