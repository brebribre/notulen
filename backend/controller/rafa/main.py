# main.py

from openai_qna import Qna

if __name__ == "__main__":
    # Initialize Querying instance
    q = Qna()

    # Paths to the transcript and question
    transcript_path = "transcript.txt"
    question = "When did the meeting happen? Answer only with 1 answer." #buat nyoba input

    # Call the method and print the result
    try:
        response = q.ask_question_with_transcript(transcript_path, question)
        print("Response from OpenAI:\n")
        print(response)
    except Exception as e:
        print(f"An error occurred: {e}")