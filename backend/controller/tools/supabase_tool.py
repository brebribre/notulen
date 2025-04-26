from agents import function_tool

class SupabaseTool:
    @function_tool
    def get_group_meeting_names_and_summaries(group_id: str, from_date: str = None, to_date: str = None) -> str:
        # TODO: fetch supabase meetings table based on group_id
        # TODO: Filter on summary and meeting_name and only maximum 15 recent meetings
        # TODO: Return a list of dictionaries with the meeting_name and summary
        print(f"Fetching meetings for group {group_id} from {from_date} to {to_date}")

        return [
            {"meeting_name": "Meeting Sprint 1", "summary": "Summary Sprint 1"},
            {"meeting_name": "Meeting Sprint 2", "summary": "Summary Sprint 2"},
        ]
