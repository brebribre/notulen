from typing import List, Dict, Any, Optional
from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, Form
from pydantic import BaseModel, Field
import uuid
from datetime import datetime
import traceback
from controller.supabase.supabase_utils import SupabaseController

router = APIRouter()
supabase = SupabaseController()

# Pydantic models for request/response
class AudioFileBase(BaseModel):
    bucket_name: str
    path: str
    original_filename: Optional[str] = None
    mimetype: Optional[str] = None
    size: Optional[int] = None
    meeting_datetime: Optional[datetime] = None

class AudioFileCreate(AudioFileBase):
    pass

class AudioFileUpdate(BaseModel):
    original_filename: Optional[str] = None
    meeting_datetime: Optional[datetime] = None

class AudioFile(AudioFileBase):
    id: uuid.UUID
    user_id: uuid.UUID
    created_at: datetime

    class Config:
        orm_mode = True

# CRUD Routes
@router.post("/audio-files", response_model=AudioFile)
async def create_audio_file(audio_file: AudioFileCreate, user_id: uuid.UUID):
    """
    Create a new audio file record.
    """
    try:
        # Create the audio file record
        file_data = {
            "user_id": str(user_id),
            "bucket_name": audio_file.bucket_name,
            "path": audio_file.path,
            "original_filename": audio_file.original_filename,
            "mimetype": audio_file.mimetype,
            "size": audio_file.size,
            "meeting_datetime": audio_file.meeting_datetime.isoformat() if audio_file.meeting_datetime else None
        }
        
        result = supabase.insert("audio_files", file_data)
        
        if not result or not result[0]:
            raise HTTPException(status_code=500, detail="Failed to create audio file record")
        
        return result[0]
    except Exception as e:
        print(f"Error in create_audio_file: {str(e)}")
        print(traceback.format_exc())
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/audio-files", response_model=List[AudioFile])
async def get_audio_files(user_id: Optional[uuid.UUID] = None):
    """
    Get all audio files or filter by user_id if provided.
    """
    try:
        filters = {}
        if user_id:
            filters["user_id"] = str(user_id)
        
        result = supabase.select(
            "audio_files", 
            "*", 
            filters=filters,
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
        result = supabase.select(
            "audio_files",
            "*",
            filters={"id": str(file_id)}
        )
        
        if not result or not result[0]:
            raise HTTPException(status_code=404, detail="Audio file not found")
        
        return result[0]
    except HTTPException as e:
        raise e
    except Exception as e:
        print(f"Error in get_audio_file: {str(e)}")
        print(traceback.format_exc())
        raise HTTPException(status_code=400, detail=str(e))

@router.put("/audio-files/{file_id}", response_model=AudioFile)
async def update_audio_file(file_id: uuid.UUID, audio_file: AudioFileUpdate, user_id: uuid.UUID):
    """
    Update an audio file record.
    """
    try:
        # Check if user owns this file
        file_check = supabase.select(
            "audio_files",
            "*",
            filters={"id": str(file_id), "user_id": str(user_id)}
        )
        
        if not file_check:
            raise HTTPException(status_code=403, detail="You don't have permission to update this file")
        
        # Prepare update data (only non-None fields)
        update_data = {}
        if audio_file.original_filename is not None:
            update_data["original_filename"] = audio_file.original_filename
        if audio_file.meeting_datetime is not None:
            update_data["meeting_datetime"] = audio_file.meeting_datetime.isoformat()
        
        if not update_data:
            # Nothing to update
            result = supabase.select("audio_files", "*", filters={"id": str(file_id)})
            return result[0] if result else None
        
        # Update the audio file record
        result = supabase.update(
            "audio_files",
            update_data,
            filters={"id": str(file_id)}
        )
        
        if not result or not result[0]:
            raise HTTPException(status_code=404, detail="Audio file not found")
        
        return result[0]
    except HTTPException as e:
        raise e
    except Exception as e:
        print(f"Error in update_audio_file: {str(e)}")
        print(traceback.format_exc())
        raise HTTPException(status_code=400, detail=str(e))

@router.delete("/audio-files/{file_id}")
async def delete_audio_file(file_id: uuid.UUID, user_id: uuid.UUID):
    """
    Delete an audio file record and the actual file from storage.
    """
    try:
        # Check if user owns this file
        file_check = supabase.select(
            "audio_files",
            "*",
            filters={"id": str(file_id), "user_id": str(user_id)}
        )
        
        if not file_check or not file_check[0]:
            raise HTTPException(status_code=403, detail="You don't have permission to delete this file")
        
        file_info = file_check[0]
        
        # Delete the file from storage
        try:
            storage_path = file_info.get("path")
            bucket_name = file_info.get("bucket_name")
            
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
    except HTTPException as e:
        raise e
    except Exception as e:
        print(f"Error in delete_audio_file: {str(e)}")
        print(traceback.format_exc())
        raise HTTPException(status_code=400, detail=str(e))

# File upload endpoint
@router.post("/upload-audio", response_model=AudioFile)
async def upload_audio_file(
    file: UploadFile = File(...),
    user_id: str = Form(...),
    meeting_datetime: Optional[str] = Form(None)
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
        unique_filename = f"{user_id}_{timestamp}_{original_filename}"
        bucket_name = "audio-files"
        
        # Upload to Supabase Storage
        supabase.client.storage.from_(bucket_name).upload(
            unique_filename,
            file_content
        )
        
        # Create database record
        file_data = {
            "user_id": user_id,
            "bucket_name": bucket_name,
            "path": unique_filename,
            "original_filename": original_filename,
            "mimetype": mimetype,
            "size": file_size,
            "meeting_datetime": meeting_datetime
        }
        
        result = supabase.insert("audio_files", file_data)
        
        if not result or not result[0]:
            # If DB insert fails, try to clean up the storage
            try:
                supabase.client.storage.from_(bucket_name).remove([unique_filename])
            except:
                pass
            raise HTTPException(status_code=500, detail="Failed to create audio file record")
        
        return result[0]
    except Exception as e:
        print(f"Error in upload_audio_file: {str(e)}")
        print(traceback.format_exc())
        raise HTTPException(status_code=400, detail=str(e))

# Get download URL
@router.get("/audio-files/{file_id}/download-url")
async def get_download_url(file_id: uuid.UUID, user_id: uuid.UUID):
    """
    Get a download URL for an audio file.
    """
    try:
        # Check if user has access to this file
        file_check = supabase.select(
            "audio_files",
            "*",
            filters={"id": str(file_id)}
        )
        
        if not file_check or not file_check[0]:
            raise HTTPException(status_code=404, detail="Audio file not found")
        
        file_info = file_check[0]
        
        # Check if the user is the owner
        if str(file_info.get("user_id")) != str(user_id):
            raise HTTPException(status_code=403, detail="You don't have permission to access this file")
        
        bucket_name = file_info.get("bucket_name")
        path = file_info.get("path")
        
        # Generate a public URL (you can set expiry if needed)
        url = supabase.client.storage.from_(bucket_name).get_public_url(path)
        
        return {"url": url}
    except HTTPException as e:
        raise e
    except Exception as e:
        print(f"Error in get_download_url: {str(e)}")
        print(traceback.format_exc())
        raise HTTPException(status_code=400, detail=str(e))
