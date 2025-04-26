from typing import List, Dict, Any, Optional
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
import uuid
from datetime import datetime
from controller.supabase.supabase_utils import SupabaseController

router = APIRouter()
supabase = SupabaseController()

# Pydantic models for request/response
class GroupBase(BaseModel):
    name: str
    description: Optional[str] = None

class GroupCreate(GroupBase):
    pass

class GroupUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None

class UserGroup(BaseModel):
    user_id: uuid.UUID
    group_id: uuid.UUID
    role: Optional[str] = "member"

class Group(GroupBase):
    id: uuid.UUID
    created_at: datetime
    created_by: uuid.UUID

    class Config:
        orm_mode = True

# CRUD Routes
@router.post("/groups", response_model=Group)
async def create_group(group: GroupCreate, user_id: uuid.UUID):
    """
    Create a new group.
    """
    try:
        # Create the group
        group_data = {
            "name": group.name,
            "description": group.description,
            "created_by": str(user_id)
        }
        
        result = supabase.insert("groups", group_data)
        
        if not result or not result[0]:
            raise HTTPException(status_code=500, detail="Failed to create group")
        
        new_group = result[0]
        
        # Add the creator as a member with 'admin' role
        user_group_data = {
            "user_id": str(user_id),
            "group_id": new_group["id"],
            "role": "admin"
        }
        
        supabase.insert("user_groups", user_group_data)
        
        return new_group
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/groups", response_model=List[Group])
async def get_groups(user_id: Optional[uuid.UUID] = None):
    """
    Get all groups or filter by user_id if provided.
    """
    try:
        if user_id:
            # First get the group IDs the user is a member of
            user_groups = supabase.select(
                "user_groups",
                "*",
                filters={"user_id": str(user_id)}
            )
            
            if not user_groups:
                return []
            
            # Extract group IDs
            group_ids = [ug.get("group_id") for ug in user_groups if ug.get("group_id")]
            
            # Get all groups
            all_groups = supabase.select(
                "groups", 
                "*", 
                order_by={"created_at": "desc"}
            )
            
            # Filter groups by IDs the user is a member of
            result = [g for g in all_groups if g.get("id") in group_ids]
            
            # Sort by created_at in descending order
            result.sort(key=lambda x: x.get("created_at", ""), reverse=True)
        else:
            # Get all groups
            result = supabase.select(
                "groups", 
                "*", 
                order_by={"created_at": "desc"}
            )
        
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/groups/{group_id}", response_model=Group)
async def get_group(group_id: uuid.UUID):
    """
    Get a specific group by ID.
    """
    try:
        result = supabase.select(
            "groups",
            "*",
            filters={"id": str(group_id)}
        )
        
        if not result or not result[0]:
            raise HTTPException(status_code=404, detail="Group not found")
        
        return result[0]
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.put("/groups/{group_id}", response_model=Group)
async def update_group(group_id: uuid.UUID, group: GroupUpdate, user_id: uuid.UUID):
    """
    Update a group.
    """
    try:
        # Check if user has admin rights for this group
        admin_check = supabase.select(
            "user_groups",
            "*",
            filters={"user_id": str(user_id), "group_id": str(group_id), "role": "admin"}
        )
        
        if not admin_check:
            raise HTTPException(status_code=403, detail="Only group admins can update group details")
        
        # Prepare update data (only non-None fields)
        update_data = {}
        if group.name is not None:
            update_data["name"] = group.name
        if group.description is not None:
            update_data["description"] = group.description
        
        if not update_data:
            # Nothing to update
            result = supabase.select("groups", "*", filters={"id": str(group_id)})
            return result[0] if result else None
        
        # Update the group
        result = supabase.update(
            "groups",
            update_data,
            filters={"id": str(group_id)}
        )
        
        if not result or not result[0]:
            raise HTTPException(status_code=404, detail="Group not found")
        
        return result[0]
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.delete("/groups/{group_id}")
async def delete_group(group_id: uuid.UUID, user_id: uuid.UUID):
    """
    Delete a group.
    """
    try:
        # Check if user has admin rights for this group
        admin_check = supabase.select(
            "user_groups",
            "*",
            filters={"user_id": str(user_id), "group_id": str(group_id), "role": "admin"}
        )
        
        if not admin_check:
            raise HTTPException(status_code=403, detail="Only group admins can delete the group")
        
        # Delete all user-group associations first
        supabase.delete(
            "user_groups",
            filters={"group_id": str(group_id)}
        )
        
        # Then delete the group
        result = supabase.delete(
            "groups",
            filters={"id": str(group_id)}
        )
        
        if not result:
            raise HTTPException(status_code=404, detail="Group not found")
        
        return {"success": True, "message": "Group deleted successfully"}
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# User-Group membership management
@router.post("/groups/{group_id}/members")
async def add_user_to_group(group_id: uuid.UUID, member: UserGroup, admin_id: uuid.UUID):
    """
    Add a user to a group.
    """
    try:
        # Check if the admin has rights to add members
        admin_check = supabase.select(
            "user_groups",
            "*",
            filters={"user_id": str(admin_id), "group_id": str(group_id), "role": "admin"}
        )
        
        if not admin_check:
            raise HTTPException(status_code=403, detail="Only group admins can add members")
        
        # Add the user to the group
        user_group_data = {
            "user_id": str(member.user_id),
            "group_id": str(group_id),
            "role": member.role or "member"
        }
        
        result = supabase.insert("user_groups", user_group_data)
        
        return {"success": True, "message": "User added to group successfully"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.delete("/groups/{group_id}/members/{user_id}")
async def remove_user_from_group(group_id: uuid.UUID, user_id: uuid.UUID, admin_id: uuid.UUID):
    """
    Remove a user from a group.
    """
    try:
        # Check if the admin has rights or if it's the user themselves leaving
        if str(admin_id) != str(user_id):
            admin_check = supabase.select(
                "user_groups",
                "*",
                filters={"user_id": str(admin_id), "group_id": str(group_id), "role": "admin"}
            )
            
            if not admin_check:
                raise HTTPException(status_code=403, detail="Only group admins can remove members")
        
        # Remove the user from the group
        result = supabase.delete(
            "user_groups",
            filters={"user_id": str(user_id), "group_id": str(group_id)}
        )
        
        if not result:
            raise HTTPException(status_code=404, detail="User not found in group")
        
        return {"success": True, "message": "User removed from group successfully"}
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/groups/{group_id}/members")
async def get_group_members(group_id: uuid.UUID):
    """
    Get all members of a group.
    """
    try:
        # First, get all user_group relationships for this group
        user_groups = supabase.select(
            "user_groups",
            "*",
            filters={"group_id": str(group_id)},
            order_by={"joined_at": "asc"}
        )
        
        if not user_groups:
            return []
        
        # Get user information from the auth admin API
        response = supabase.client.auth.admin.list_users()
        
        if hasattr(response, "users"):
            users = response.users
        elif hasattr(response, "data") and hasattr(response.data, "users"):
            users = response.data.users
        else:
            users = []
            
        # Create a dictionary of users for fast lookup
        users_dict = {}
        for user in users:
            user_data = {
                "id": user.id,
                "email": user.email,
                "name": None
            }
            
            # Extract name from user metadata if available
            if hasattr(user, "user_metadata") and user.user_metadata:
                if isinstance(user.user_metadata, dict) and "name" in user.user_metadata:
                    user_data["name"] = user.user_metadata["name"]
                    
            users_dict[user.id] = user_data
        
        # Combine user_groups with user information
        result = []
        for ug in user_groups:
            user_id = ug.get("user_id")
            if user_id in users_dict:
                member_data = {
                    "user_id": user_id,
                    "role": ug.get("role"),
                    "joined_at": ug.get("joined_at"),
                    "email": users_dict[user_id]["email"],
                    "name": users_dict[user_id]["name"]
                }
                result.append(member_data)
        
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
