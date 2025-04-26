from typing import List, Dict, Any, Optional
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
import uuid
from datetime import datetime
from controller.supabase.supabase_utils import SupabaseController

router = APIRouter()
supabase = SupabaseController()

class User(BaseModel):
    id: uuid.UUID
    email: str
    name: Optional[str] = None
    created_at: datetime

@router.get("/users/{user_id}", response_model=Dict[str, Any])
async def get_user(user_id: uuid.UUID):
    """
    Get a specific user by ID.
    """
    try:
        # For Supabase, we need to use the client directly for auth tables
        response = supabase.client.auth.admin.get_user_by_id(str(user_id))
        
        if not response or not hasattr(response, "user"):
            raise HTTPException(status_code=404, detail="User not found")
        
        user = response.user
        
        user_data = {
            "id": user.id,
            "email": user.email,
            "created_at": user.created_at,
            "name": None,
            "avatar_url": None
        }
        
        # Extract additional fields from user metadata if available
        if hasattr(user, "user_metadata") and user.user_metadata:
            if isinstance(user.user_metadata, dict):
                if "name" in user.user_metadata:
                    user_data["name"] = user.user_metadata["name"]
                if "avatar_url" in user.user_metadata:
                    user_data["avatar_url"] = user.user_metadata["avatar_url"]
        
        return user_data
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

#TODO: Add a route to get all users or by email (for add user to group)