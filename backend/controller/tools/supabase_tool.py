from agents import function_tool
from controller.supabase.supabase_utils import SupabaseController
from typing import List, Dict, Any, Optional
import json
from datetime import datetime

# Initialize the Supabase controller
supabase = SupabaseController()

class SupabaseTool:
    @function_tool
    def get_group_meeting_names_and_summaries(group_id: str, from_date: str = None, to_date: str = None) -> str:
        """
        Fetch meeting names and summaries for a specific group, with optional date filtering.
        
        Args:
            group_id: The ID of the group to fetch meetings for
            from_date: Optional start date in ISO format (YYYY-MM-DD)
            to_date: Optional end date in ISO format (YYYY-MM-DD)
            
        Returns:
            JSON string of meeting data with names and summaries
        """
        print(f"Fetching meetings for group {group_id} from {from_date} to {to_date}")
        
        # Start building filters
        filters = {"group_id": group_id}
        
        # Note: Date filtering in select is limited, but we'll fetch more data 
        # and filter after the fact to get the most recent 15 with summaries
        
        # Fetch meetings for the group
        meetings = supabase.select(
            "meetings",
            "id, name, meeting_datetime, summary",
            filters=filters,
            order_by={"meeting_datetime": "desc"},
            limit=30  # Fetch more than needed to account for filtering
        )
        
        print(f"Found {len(meetings)} meetings")
        
        # Convert from_date and to_date strings to datetime objects if provided
        from_datetime = None
        to_datetime = None
        
        if from_date:
            try:
                # Parse the from_date into a datetime object - just the date portion
                from_datetime = datetime.fromisoformat(from_date.split('T')[0]) if 'T' in from_date else datetime.fromisoformat(from_date)
                print(f"Parsed from_date: {from_datetime}")
            except ValueError as e:
                print(f"Error parsing from_date '{from_date}': {str(e)}")
        
        if to_date:
            try:
                # Parse the to_date into a datetime object - just the date portion
                to_datetime = datetime.fromisoformat(to_date.split('T')[0]) if 'T' in to_date else datetime.fromisoformat(to_date)
                # Set time to end of day for inclusive comparison
                print(f"Parsed to_date: {to_datetime}")
            except ValueError as e:
                print(f"Error parsing to_date '{to_date}': {str(e)}")
        
        # Process the results and apply date filtering in Python
        result = []
        for meeting in meetings:
            meeting_datetime_str = meeting.get("meeting_datetime")
            
            # Skip if missing datetime and we have date filters
            if not meeting_datetime_str and (from_datetime or to_datetime):
                continue
                
            # Convert meeting datetime string to datetime object
            if meeting_datetime_str:
                try:
                    # Handle different ISO formats
                    meeting_datetime = datetime.fromisoformat(meeting_datetime_str.replace('Z', '+00:00') if meeting_datetime_str.endswith('Z') else meeting_datetime_str)
                    
                    # Apply date filters if specified
                    if from_datetime and meeting_datetime.date() < from_datetime.date():
                        continue
                    if to_datetime and meeting_datetime.date() > to_datetime.date():
                        continue
                except ValueError as e:
                    print(f"Error parsing meeting_datetime '{meeting_datetime_str}': {str(e)}")
                    # Skip if we can't parse the date and date filters are specified
                    if from_datetime or to_datetime:
                        continue
                
            # Only include meetings that have a summary
            summary = meeting.get("summary")
            if summary and isinstance(summary, dict) and summary.get("summary"):
                meeting_summary = {
                    "meeting_name": meeting.get("name", "Untitled Meeting"),
                    "summary": summary.get("summary", "")
                }
                result.append(meeting_summary)
                
            # Stop once we have 15 meetings with summaries
            if len(result) >= 15:
                break
        
        print(f"Found {len(result)} meetings after filtering")
        # Return as JSON string
        return json.dumps(result)
