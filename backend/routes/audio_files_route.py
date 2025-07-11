from typing import List, Dict, Any, Optional
from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, Form
from pydantic import BaseModel, Field
import uuid
from datetime import datetime
import traceback
import httpx
from controller.supabase.supabase_utils import SupabaseController
from controller.marcel.speech_to_text import SpeechToText
from controller.cede.openai_summary_async import AsyncTranscriptSummarizer

router = APIRouter()
supabase = SupabaseController()
speech_to_text = SpeechToText()
transcript_summarizer = AsyncTranscriptSummarizer()

# Pydantic models for request/response
class AudioFileBase(BaseModel):
    bucket_name: str
    path: str
    original_filename: Optional[str] = None
    mimetype: Optional[str] = None
    size: Optional[int] = None
    meeting_datetime: Optional[datetime] = None
    meeting_id: Optional[uuid.UUID] = None

class AudioFileCreate(AudioFileBase):
    group_id: uuid.UUID

class AudioFileUpdate(BaseModel):
    original_filename: Optional[str] = None
    meeting_datetime: Optional[datetime] = None
    meeting_id: Optional[uuid.UUID] = None

class AudioFile(AudioFileBase):
    id: uuid.UUID
    group_id: uuid.UUID
    created_at: datetime

    class Config:
        orm_mode = True

# CRUD Routes
@router.post("/audio-files", response_model=AudioFile)
async def create_audio_file(audio_file: AudioFileCreate):
    """
    Create a new audio file record associated with a group.
    """
    try:
        # Create the audio file record
        file_data = {
            "group_id": str(audio_file.group_id),
            "bucket_name": audio_file.bucket_name,
            "path": audio_file.path,
            "original_filename": audio_file.original_filename,
            "mimetype": audio_file.mimetype,
            "size": audio_file.size,
            "meeting_datetime": audio_file.meeting_datetime.isoformat() if audio_file.meeting_datetime else None
        }
        
        # Add meeting_id if provided
        if audio_file.meeting_id:
            file_data["meeting_id"] = str(audio_file.meeting_id)
        
        result = supabase.insert("audio_files", file_data)

        # TODO: process file
        
        if not result or not result[0]:
            raise HTTPException(status_code=500, detail="Failed to create audio file record")
        
        return result[0]
    except Exception as e:
        print(f"Error in create_audio_file: {str(e)}")
        print(traceback.format_exc())
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/audio-files", response_model=List[AudioFile])
async def get_audio_files(group_id: uuid.UUID):
    """
    Get all audio files for a specific group.
    """
    try:
        if not group_id:
            raise HTTPException(status_code=400, detail="Group ID is required")
        
        # Get audio files for the group
        result = supabase.select(
            "audio_files", 
            "*", 
            filters={"group_id": str(group_id)},
            order_by={"created_at": "desc"}
        )
        
        return result
    except Exception as e:
        print(f"Error in get_audio_files: {str(e)}")
        print(traceback.format_exc())
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/audio-files/{file_id}", response_model=AudioFile)
async def get_audio_file(file_id: uuid.UUID):
    """
    Get a specific audio file by ID.
    """
    try:
        # Get the file information
        file_info = supabase.select(
            "audio_files",
            "*",
            filters={"id": str(file_id)}
        )
        
        if not file_info or not file_info[0]:
            raise HTTPException(status_code=404, detail="Audio file not found")
        
        return file_info[0]
    except Exception as e:
        print(f"Error in get_audio_file: {str(e)}")
        print(traceback.format_exc())
        raise HTTPException(status_code=400, detail=str(e))

@router.put("/audio-files/{file_id}", response_model=AudioFile)
async def update_audio_file(file_id: uuid.UUID, audio_file: AudioFileUpdate):
    """
    Update an audio file's metadata.
    """
    try:
        # Get the file information
        file_info = supabase.select(
            "audio_files",
            "*",
            filters={"id": str(file_id)}
        )
        
        if not file_info or not file_info[0]:
            raise HTTPException(status_code=404, detail="Audio file not found")
        
        # Prepare update data (only non-None fields)
        update_data = {}
        if audio_file.original_filename is not None:
            update_data["original_filename"] = audio_file.original_filename
        if audio_file.meeting_datetime is not None:
            update_data["meeting_datetime"] = audio_file.meeting_datetime.isoformat()
        if audio_file.meeting_id is not None:
            update_data["meeting_id"] = str(audio_file.meeting_id)
        
        if not update_data:
            # Nothing to update
            return file_info[0]
        
        # Update the audio file record
        result = supabase.update(
            "audio_files",
            update_data,
            filters={"id": str(file_id)}
        )
        
        if not result or not result[0]:
            raise HTTPException(status_code=404, detail="Audio file not found")
        
        return result[0]
    except Exception as e:
        print(f"Error in update_audio_file: {str(e)}")
        print(traceback.format_exc())
        raise HTTPException(status_code=400, detail=str(e))

@router.delete("/audio-files/{file_id}")
async def delete_audio_file(file_id: uuid.UUID):
    """
    Delete an audio file record and the actual file from storage.
    """
    try:
        # Get the file information
        file_info = supabase.select(
            "audio_files",
            "*",
            filters={"id": str(file_id)}
        )
        
        if not file_info or not file_info[0]:
            raise HTTPException(status_code=404, detail="Audio file not found")
        
        # Delete the file from storage
        try:
            storage_path = file_info[0].get("path")
            bucket_name = file_info[0].get("bucket_name")
            
            # Remove the file from storage
            supabase.client.storage.from_(bucket_name).remove([storage_path])
        except Exception as storage_error:
            print(f"Warning: Could not delete file from storage: {str(storage_error)}")
            # Continue with deleting the database record even if storage deletion fails
        
        # Delete the database record
        result = supabase.delete(
            "audio_files",
            filters={"id": str(file_id)}
        )
        
        if not result:
            raise HTTPException(status_code=404, detail="Audio file record not found")
        
        return {"success": True, "message": "Audio file deleted successfully"}
    except Exception as e:
        print(f"Error in delete_audio_file: {str(e)}")
        print(traceback.format_exc())
        raise HTTPException(status_code=400, detail=str(e))

# File upload endpoint
@router.post("/upload-audio", response_model=AudioFile)
async def upload_audio_file(
    file: UploadFile = File(...),
    group_id: str = Form(...),
    meeting_datetime: Optional[str] = Form(None),
    meeting_id: Optional[str] = Form(None)
):
    """
    Upload an audio file to storage and create a record in the database.
    """
    try:
        # Read file content
        file_content = await file.read()
        file_size = len(file_content)
        
        # Get file info
        original_filename = file.filename
        mimetype = file.content_type
        
        # Create a unique path for the file
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        unique_filename = f"group_{group_id}_{timestamp}_{original_filename}"
        bucket_name = "audio-files"
        
        # Upload to Supabase Storage
        supabase.client.storage.from_(bucket_name).upload(
            unique_filename,
            file_content
        )
        
        # Create database record
        file_data = {
            "group_id": group_id,
            "bucket_name": bucket_name,
            "path": unique_filename,
            "original_filename": original_filename,
            "mimetype": mimetype,
            "size": file_size,
            "meeting_datetime": meeting_datetime
        }
        
        # Add meeting_id if provided
        if meeting_id:
            file_data["meeting_id"] = meeting_id
        
        result = supabase.insert("audio_files", file_data)
        
        if not result or not result[0]:
            # If DB insert fails, try to clean up the storage
            try:
                supabase.client.storage.from_(bucket_name).remove([unique_filename])
            except:
                pass
            raise HTTPException(status_code=500, detail="Failed to create audio file record")
        
        # Call the background worker to process the audio file
        try:
            file_id = result[0]["id"]
            async with httpx.AsyncClient() as client:
                # Call the worker endpoint to start background processing
                worker_url = f"http://127.0.0.1:5000/audio-files/{file_id}/bytes"
                worker_response = await client.get(worker_url)
                
                if worker_response.status_code != 202:
                    print(f"Warning: Background worker returned status {worker_response.status_code}")
                    print(f"Response: {worker_response.text}")
                else:
                    print(f"Successfully triggered background processing for file {file_id}")
        except Exception as worker_error:
            # Log the error but don't fail the upload
            print(f"Warning: Could not call background worker: {str(worker_error)}")
            print(traceback.format_exc())

        return result[0]
    except Exception as e:
        print(f"Error in upload_audio_file: {str(e)}")
        print(traceback.format_exc())
        raise HTTPException(status_code=400, detail=str(e))

# Get download URL
@router.get("/audio-files/{file_id}/download-url")
async def get_download_url(file_id: uuid.UUID):
    """
    Get a download URL for an audio file.
    """
    try:
        # Get the file information
        file_info = supabase.select(
            "audio_files",
            "*",
            filters={"id": str(file_id)}
        )
        
        if not file_info or not file_info[0]:
            raise HTTPException(status_code=404, detail="Audio file not found")
        
        bucket_name = file_info[0].get("bucket_name")
        path = file_info[0].get("path")
        
        # Generate a signed URL (with expiration time of 1 hour)
        url_result = supabase.get_signed_url(bucket_name, path, 3600)
        
        if not url_result or "signedURL" not in url_result:
            raise HTTPException(status_code=500, detail="Failed to generate signed URL")
            
        return {"url": url_result["signedURL"]}
    except Exception as e:
        print(f"Error in get_download_url: {str(e)}")
        print(traceback.format_exc())
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/meetings/{meeting_id}/audio-files", response_model=List[AudioFile])
async def get_meeting_audio_files(meeting_id: uuid.UUID):
    """
    Get all audio files for a specific meeting.
    """
    try:
        if not meeting_id:
            raise HTTPException(status_code=400, detail="Meeting ID is required")
        
        # Get audio files for the meeting
        result = supabase.select(
            "audio_files", 
            "*", 
            filters={"meeting_id": str(meeting_id)},
            order_by={"created_at": "desc"}
        )
        
        return result
    except Exception as e:
        print(f"Error in get_meeting_audio_files: {str(e)}")
        print(traceback.format_exc())
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/audio-files/{file_id}/assign-to-meeting", response_model=AudioFile)
async def assign_audio_to_meeting(file_id: uuid.UUID, meeting_data: Dict[str, str]):
    """
    Assign an existing audio file to a meeting.
    """
    try:
        meeting_id = meeting_data.get("meeting_id")
        if not meeting_id:
            raise HTTPException(status_code=400, detail="Meeting ID is required")
            
        # Get the file information
        file_info = supabase.select(
            "audio_files",
            "*",
            filters={"id": str(file_id)}
        )
        
        if not file_info or not file_info[0]:
            raise HTTPException(status_code=404, detail="Audio file not found")
        
        # Update the audio file record
        result = supabase.update(
            "audio_files",
            {"meeting_id": meeting_id},
            filters={"id": str(file_id)}
        )
        
        if not result or not result[0]:
            raise HTTPException(status_code=404, detail="Audio file not found after update")
        
        return result[0]
    except Exception as e:
        print(f"Error in assign_audio_to_meeting: {str(e)}")
        print(traceback.format_exc())
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/audio-files/by-meeting", response_model=List[AudioFile])
async def get_audio_files_by_meeting(meeting_id: uuid.UUID):
    """
    Get all audio files for a specific meeting using query parameters.
    This is an alternative to the /meetings/{meeting_id}/audio-files endpoint.
    """
    try:
        if not meeting_id:
            raise HTTPException(status_code=400, detail="Meeting ID is required")
        
        # Get audio files for the meeting
        result = supabase.select(
            "audio_files", 
            "*", 
            filters={"meeting_id": str(meeting_id)},
            order_by={"created_at": "desc"}
        )
        
        return result
    except Exception as e:
        print(f"Error in get_audio_files_by_meeting: {str(e)}")
        print(traceback.format_exc())
        raise HTTPException(status_code=400, detail=str(e))
