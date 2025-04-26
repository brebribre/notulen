from typing import Optional
from fastapi import APIRouter, HTTPException, UploadFile, File, Form, Response, BackgroundTasks
import uuid
from datetime import datetime
import traceback
from controller.supabase.supabase_utils import SupabaseController
from controller.marcel.speech_to_text import SpeechToText
from controller.cede.openai_summary_async import AsyncTranscriptSummarizer

router = APIRouter()
supabase = SupabaseController()
speech_to_text = SpeechToText()
transcript_summarizer = AsyncTranscriptSummarizer()

async def process_audio_file(file_id: uuid.UUID):
    """
    Background task to process the audio file and generate transcript and summary.
    """
    try:
        # Get the file information
        file_info = supabase.select(
            "audio_files",
            "*",
            filters={"id": str(file_id)}
        )
        
        if not file_info or not file_info[0]:
            print(f"Error: Audio file {file_id} not found")
            return
        
        # Get file info from the database
        bucket_name = file_info[0].get("bucket_name")
        storage_path = file_info[0].get("path")
        meeting_id = file_info[0].get("meeting_id")
        
        # Download the file from Supabase Storage
        try:
            file_bytes = supabase.client.storage.from_(bucket_name).download(storage_path)
            
            # Process the audio file into transcript and summary
            transcript = speech_to_text.speech_to_text_from_bytes(file_bytes)
            print(f"Transcript: {transcript}")
            
            summary = await transcript_summarizer.summarize_async(transcript)
            print(f"Summary: {summary}")
            
            # Update the meetings table's transcript and summary columns if meeting_id is provided
            if meeting_id:
                # Convert summary to appropriate format for storage
                summary_json = {
                    "summary": summary.summary,
                    "action_items": summary.action_items,
                    "participants": summary.participants
                }
                
                # Update the meeting record in Supabase
                meeting_update = {
                    "transcript": transcript,
                    "summary": summary_json
                }
                
                meeting_result = supabase.update(
                    "meetings",
                    meeting_update,
                    filters={"id": meeting_id}
                )
                
                if not meeting_result:
                    print(f"Warning: Could not update meeting {meeting_id} with transcript and summary.")
                else:
                    print(f"Successfully updated meeting {meeting_id} with transcript and summary.")
            
        except Exception as storage_error:
            print(f"Error downloading file from storage: {str(storage_error)}")
            
    except Exception as e:
        print(f"Error in process_audio_file: {str(e)}")
        print(traceback.format_exc())

@router.get("/audio-files/{file_id}/bytes")
async def get_audio_file_bytes(file_id: uuid.UUID, background_tasks: BackgroundTasks):
    """
    Process the audio file by ID to generate transcript and summary as a background task.
    """
    try:
        # Get the file information to validate the file exists
        file_info = supabase.select(
            "audio_files",
            "*",
            filters={"id": str(file_id)}
        )
        
        if not file_info or not file_info[0]:
            raise HTTPException(status_code=404, detail="Audio file not found")
        
        # Add the processing to background tasks
        background_tasks.add_task(process_audio_file, file_id)
        
        # Return immediately with a 202 Accepted status
        return Response(status_code=202)
        
    except Exception as e:
        print(f"Error in get_audio_file_bytes: {str(e)}")
        print(traceback.format_exc())
        raise HTTPException(status_code=400, detail=str(e))
