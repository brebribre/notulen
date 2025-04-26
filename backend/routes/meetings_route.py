from typing import List, Dict, Any, Optional
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
import uuid
from datetime import datetime
from controller.supabase.supabase_utils import SupabaseController
import traceback

router = APIRouter()
supabase = SupabaseController()

# Pydantic models for request/response
class MeetingBase(BaseModel):
    group_id: uuid.UUID
    meeting_datetime: datetime
    transcript: Optional[str] = None
    summary: Optional[Dict[str, Any]] = None

class MeetingCreate(MeetingBase):
    pass

class MeetingUpdate(BaseModel):
    meeting_datetime: Optional[datetime] = None
    transcript: Optional[str] = None
    summary: Optional[Dict[str, Any]] = None

class Meeting(MeetingBase):
    id: uuid.UUID
    created_at: datetime

    class Config:
        orm_mode = True

# CRUD Routes
@router.post("/meetings", response_model=Meeting)
async def create_meeting(meeting: MeetingCreate, user_id: uuid.UUID):
    """
    Create a new meeting.
    """
    try:
        # Check if user has rights to create a meeting in this group
        user_group = supabase.select(
            "user_groups",
            "*",
            filters={"user_id": str(user_id), "group_id": str(meeting.group_id)}
        )
        
        if not user_group:
            raise HTTPException(status_code=403, detail="You must be a member of the group to create a meeting")
        
        # Create the meeting
        meeting_data = {
            "group_id": str(meeting.group_id),
            "meeting_datetime": meeting.meeting_datetime.isoformat(),
            "transcript": meeting.transcript,
            "summary": meeting.summary
        }
        
        result = supabase.insert("meetings", meeting_data)
        
        if not result or not result[0]:
            raise HTTPException(status_code=500, detail="Failed to create meeting")
        
        return result[0]
    except HTTPException as e:
        raise e
    except Exception as e:
        print(f"Error in create_meeting: {str(e)}")
        print(traceback.format_exc())
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/meetings", response_model=List[Meeting])
async def get_meetings(group_id: Optional[uuid.UUID] = None):
    """
    Get all meetings or filter by group_id if provided.
    """
    try:
        if group_id:
            # Get meetings for specific group
            result = supabase.select(
                "meetings",
                "*",
                filters={"group_id": str(group_id)},
                order_by={"meeting_datetime": "desc"}
            )
        else:
            # Get all meetings
            result = supabase.select(
                "meetings", 
                "*", 
                order_by={"meeting_datetime": "desc"}
            )
        
        return result
    except Exception as e:
        print(f"Error in get_meetings: {str(e)}")
        print(traceback.format_exc())
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/meetings/{meeting_id}", response_model=Meeting)
async def get_meeting(meeting_id: uuid.UUID, user_id: uuid.UUID):
    """
    Get a specific meeting by ID.
    """
    try:
        # Get the meeting
        meeting = supabase.select(
            "meetings",
            "*",
            filters={"id": str(meeting_id)}
        )
        
        if not meeting or not meeting[0]:
            raise HTTPException(status_code=404, detail="Meeting not found")
        
        # Check if user has access to this meeting
        group_id = meeting[0].get("group_id")
        user_group = supabase.select(
            "user_groups",
            "*",
            filters={"user_id": str(user_id), "group_id": group_id}
        )
        
        if not user_group:
            raise HTTPException(status_code=403, detail="You must be a member of the group to view this meeting")
        
        return meeting[0]
    except HTTPException as e:
        raise e
    except Exception as e:
        print(f"Error in get_meeting: {str(e)}")
        print(traceback.format_exc())
        raise HTTPException(status_code=400, detail=str(e))

@router.put("/meetings/{meeting_id}", response_model=Meeting)
async def update_meeting(meeting_id: uuid.UUID, meeting: MeetingUpdate, user_id: uuid.UUID):
    """
    Update a meeting.
    """
    try:
        # Get the meeting to check group access
        current_meeting = supabase.select(
            "meetings",
            "*",
            filters={"id": str(meeting_id)}
        )
        
        if not current_meeting or not current_meeting[0]:
            raise HTTPException(status_code=404, detail="Meeting not found")
        
        group_id = current_meeting[0].get("group_id")
        
        # Check if user has admin rights for this group
        admin_check = supabase.select(
            "user_groups",
            "*",
            filters={"user_id": str(user_id), "group_id": group_id, "role": "admin"}
        )
        
        if not admin_check:
            raise HTTPException(status_code=403, detail="Only group admins can update meetings")
        
        # Prepare update data (only non-None fields)
        update_data = {}
        if meeting.meeting_datetime is not None:
            update_data["meeting_datetime"] = meeting.meeting_datetime.isoformat()
        if meeting.transcript is not None:
            update_data["transcript"] = meeting.transcript
        if meeting.summary is not None:
            update_data["summary"] = meeting.summary
        
        if not update_data:
            # Nothing to update
            return current_meeting[0]
        
        # Update the meeting
        result = supabase.update(
            "meetings",
            update_data,
            filters={"id": str(meeting_id)}
        )
        
        if not result or not result[0]:
            raise HTTPException(status_code=404, detail="Meeting not found after update")
        
        return result[0]
    except HTTPException as e:
        raise e
    except Exception as e:
        print(f"Error in update_meeting: {str(e)}")
        print(traceback.format_exc())
        raise HTTPException(status_code=400, detail=str(e))

@router.delete("/meetings/{meeting_id}")
async def delete_meeting(meeting_id: uuid.UUID, user_id: uuid.UUID):
    """
    Delete a meeting.
    """
    try:
        # Get the meeting to check group access
        meeting = supabase.select(
            "meetings",
            "*",
            filters={"id": str(meeting_id)}
        )
        
        if not meeting or not meeting[0]:
            raise HTTPException(status_code=404, detail="Meeting not found")
        
        group_id = meeting[0].get("group_id")
        
        # Check if user has admin rights for this group
        admin_check = supabase.select(
            "user_groups",
            "*",
            filters={"user_id": str(user_id), "group_id": group_id, "role": "admin"}
        )
        
        if not admin_check:
            raise HTTPException(status_code=403, detail="Only group admins can delete meetings")
        
        # Delete the meeting
        result = supabase.delete(
            "meetings",
            filters={"id": str(meeting_id)}
        )
        
        if not result:
            raise HTTPException(status_code=404, detail="Meeting not found during deletion")
        
        return {"success": True, "message": "Meeting deleted successfully"}
    except HTTPException as e:
        raise e
    except Exception as e:
        print(f"Error in delete_meeting: {str(e)}")
        print(traceback.format_exc())
        raise HTTPException(status_code=400, detail=str(e))
