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
        
        # Verify the user exists in the users table
        user_exists = supabase.select(
            "users",
            "*",
            filters={"id": str(member.user_id)}
        )
        
        if not user_exists:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Check if user is already a member of the group
        existing_membership = supabase.select(
            "user_groups",
            "*",
            filters={"user_id": str(member.user_id), "group_id": str(group_id)}
        )
        
        if existing_membership:
            raise HTTPException(status_code=400, detail="User is already a member of this group")
        
        # Add the user to the group
        user_group_data = {
            "user_id": str(member.user_id),
            "group_id": str(group_id),
            "role": member.role or "member"
        }
        
        result = supabase.insert("user_groups", user_group_data)
        
        return {"success": True, "message": "User added to group successfully"}
    except HTTPException as e:
        raise e
    except Exception as e:
        print(f"Error in add_user_to_group: {str(e)}")
        print(traceback.format_exc())
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
        
        # Get user information from the users table instead of auth API
        result = []
        for ug in user_groups:
            user_id = ug.get("user_id")
            if not user_id:
                continue
                
            # Get user info from the users table
            user_info = supabase.select(
                "users",
                "*",
                filters={"id": user_id}
            )
            
            if user_info and len(user_info) > 0:
                user = user_info[0]
                member_data = {
                    "user_id": user_id,
                    "role": ug.get("role"),
                    "joined_at": ug.get("joined_at"),
                    "email": user.get("email"),
                    "name": user.get("name")
                }
                result.append(member_data)
        
        return result
    except Exception as e:
        print(f"Error in get_group_members: {str(e)}")
        print(traceback.format_exc())
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/search-users")
async def search_users(search: str):
    """
    Search for users by email or name.
    Used for finding users to add to a group.
    """
    try:
        if not search or len(search.strip()) < 2:
            raise HTTPException(status_code=400, detail="Search term must be at least 2 characters")
        
        # Use Supabase select with comparison operators
        # First search by email (exact match)
        users_by_email = supabase.select(
            "users",
            "*",
            filters={"email": search}
        )
        
        # Then search by email or name (partial match)
        # This would ideally use ILIKE, but since SupabaseController doesn't support it directly,
        # we'll implement a simple client-side filter
        all_users = supabase.select(
            "users",
            "*",
            limit=100  # Limit to prevent loading too many users
        )
        
        # Filter users by search term (case insensitive)
        search_term = search.lower()
        filtered_users = []
        
        # Start with exact email matches
        for user in users_by_email:
            if user not in filtered_users:
                filtered_users.append(user)
        
        # Add partial matches
        user_ids = [user.get("id") for user in filtered_users]  # To avoid duplicates
        for user in all_users:
            if user.get("id") in user_ids:
                continue
                
            # Safely get email and name, converting None to empty string
            email = user.get("email", "") or ""
            name = user.get("name", "") or ""
            
            # Convert to lowercase for case-insensitive comparison
            email_lower = email.lower()
            name_lower = name.lower()
            
            if search_term in email_lower or search_term in name_lower:
                filtered_users.append(user)
                
        # Return the first 10 matches at most
        return filtered_users[:10]
        
    except HTTPException as e:
        raise e
    except Exception as e:
        print(f"Error in search_users: {str(e)}")
        print(traceback.format_exc())
        raise HTTPException(status_code=400, detail=str(e))
