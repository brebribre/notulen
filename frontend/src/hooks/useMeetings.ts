import { ref, computed } from 'vue'
import { useAuthStore } from '@/stores/auth'
import { useAudioFiles } from '@/hooks/useAudioFiles'

interface Meeting {
  id: string
  group_id: string
  name: string
  meeting_datetime: string
  transcript: string | null
  summary: Record<string, any> | null
  created_at: string
}

interface MeetingCreate {
  group_id: string
  name: string
  meeting_datetime: string
  transcript?: string | null
  summary?: Record<string, any> | null
}

interface MeetingUpdate {
  name?: string
  meeting_datetime?: string
  transcript?: string | null
  summary?: Record<string, any> | null
}

interface AudioFile {
  id: string
  group_id: string
  bucket_name: string
  path: string
  original_filename: string | null
  mimetype: string | null
  size: number | null
  meeting_datetime: string | null
  meeting_id: string | null
  created_at: string
}

export function useMeetings() {
  const authStore = useAuthStore()
  const { fetchMeetingAudioFiles } = useAudioFiles()
  const meetings = ref<Meeting[]>([])
  const currentMeeting = ref<Meeting | null>(null)
  const meetingAudioFiles = ref<AudioFile[]>([])
  const loading = ref(false)
  const error = ref<string | null>(null)

  const API_URL = import.meta.env.VITE_API_URL || ''
  
  const userId = computed(() => authStore.user?.id || '')

  // Helper function for API requests
  const apiRequest = async <T>(
    url: string, 
    method: string = 'GET', 
    body?: any, 
    params?: Record<string, string>
  ): Promise<T> => {
    // Construct URL with query parameters
    if (params) {
      const queryParams = new URLSearchParams()
      Object.entries(params).forEach(([key, value]) => {
        queryParams.append(key, value)
      })
      url = `${url}?${queryParams.toString()}`
    }

    // Prepare request options
    const options: RequestInit = {
      method,
      headers: {
        'Content-Type': 'application/json',
      }
    }

    // Add body for non-GET requests
    if (body && method !== 'GET') {
      options.body = JSON.stringify(body)
    }

    // Make request
    const response = await fetch(url, options)
    
    // Handle non-2xx responses
    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}))
      throw new Error(errorData.detail || `Request failed with status ${response.status}`)
    }
    
    // Parse and return response data
    return await response.json()
  }

  // Get all meetings or filter by group_id
  const fetchMeetings = async (groupId?: string) => {
    loading.value = true
    error.value = null
    
    try {
      const url = `${API_URL}/meetings`
      const params: Record<string, string> = {}
      
      if (groupId) {
        params.group_id = groupId
      }
      
      const data = await apiRequest<Meeting[]>(url, 'GET', undefined, params)
      meetings.value = data
      return data
    } catch (err: any) {
      console.error('Error fetching meetings:', err)
      error.value = err.message || 'Failed to fetch meetings'
      return []
    } finally {
      loading.value = false
    }
  }

  // Get a specific meeting by ID
  const fetchMeeting = async (meetingId: string, showLoading: boolean = true) => {
    if (showLoading) {
      loading.value = true
    }
    error.value = null
    
    try {
      const data = await apiRequest<Meeting>(
        `${API_URL}/meetings/${meetingId}`, 
        'GET',
        undefined,
        { user_id: userId.value }
      )
      currentMeeting.value = data
      return data
    } catch (err: any) {
      console.error('Error fetching meeting:', err)
      error.value = err.message || 'Failed to fetch meeting'
      return null
    } finally {
      if (showLoading) {
        loading.value = false
      }
    }
  }

  // Create a new meeting
  const createMeeting = async (meetingData: MeetingCreate) => {
    loading.value = true
    error.value = null
    
    try {
      const data = await apiRequest<Meeting>(
        `${API_URL}/meetings`, 
        'POST', 
        meetingData, 
        { user_id: userId.value }
      )
      
      // Update the meetings list if we're viewing the same group
      if (meetings.value.length > 0 && meetings.value[0].group_id === meetingData.group_id) {
        await fetchMeetings(meetingData.group_id)
      }
      
      return data
    } catch (err: any) {
      console.error('Error creating meeting:', err)
      error.value = err.message || 'Failed to create meeting'
      return null
    } finally {
      loading.value = false
    }
  }

  // Update a meeting
  const updateMeeting = async (meetingId: string, data: MeetingUpdate) => {
    loading.value = true
    error.value = null
    
    try {
      const updatedMeeting = await apiRequest<Meeting>(
        `${API_URL}/meetings/${meetingId}`, 
        'PUT', 
        data, 
        { user_id: userId.value }
      )
      
      // Update local state
      if (currentMeeting.value && currentMeeting.value.id === meetingId) {
        currentMeeting.value = updatedMeeting
      }
      
      // Update the meetings list if this meeting is in the current list
      const meetingIndex = meetings.value.findIndex(m => m.id === meetingId)
      if (meetingIndex !== -1) {
        meetings.value[meetingIndex] = updatedMeeting
        // Create a new array to trigger reactivity
        meetings.value = [...meetings.value]
      }
      
      return updatedMeeting
    } catch (err: any) {
      console.error('Error updating meeting:', err)
      error.value = err.message || 'Failed to update meeting'
      return null
    } finally {
      loading.value = false
    }
  }

  // Delete a meeting
  const deleteMeeting = async (meetingId: string) => {
    loading.value = true
    error.value = null
    
    try {
      const data = await apiRequest<{ success: boolean; message: string }>(
        `${API_URL}/meetings/${meetingId}`, 
        'DELETE', 
        undefined, 
        { user_id: userId.value }
      )
      
      // Update local state
      if (currentMeeting.value && currentMeeting.value.id === meetingId) {
        currentMeeting.value = null
      }
      
      // Remove from the meetings list if present
      meetings.value = meetings.value.filter(m => m.id !== meetingId)
      
      return data
    } catch (err: any) {
      console.error('Error deleting meeting:', err)
      error.value = err.message || 'Failed to delete meeting'
      return null
    } finally {
      loading.value = false
    }
  }

  // Clear transcript and summary for a meeting
  const clearMeetingTranscriptAndSummary = async (meetingId: string) => {
    loading.value = true
    error.value = null
    
    try {
      // Update meeting with null transcript and summary
      const updateData: MeetingUpdate = {
        transcript: "",
        summary: {}
      }
      
      const updatedMeeting = await apiRequest<Meeting>(
        `${API_URL}/meetings/${meetingId}`, 
        'PUT', 
        updateData, 
        { user_id: userId.value }
      )
      
      // Update local state
      if (currentMeeting.value && currentMeeting.value.id === meetingId) {
        currentMeeting.value = updatedMeeting
      }
      
      // Update the meetings list if this meeting is in the current list
      const meetingIndex = meetings.value.findIndex(m => m.id === meetingId)
      if (meetingIndex !== -1) {
        meetings.value[meetingIndex] = updatedMeeting
        // Create a new array to trigger reactivity
        meetings.value = [...meetings.value]
      }
      
      return updatedMeeting
    } catch (err: any) {
      console.error('Error clearing meeting transcript and summary:', err)
      error.value = err.message || 'Failed to clear meeting data'
      return null
    } finally {
      loading.value = false
    }
  }

  // Get audio files for a specific meeting
  const getMeetingAudioFiles = async (meetingId: string) => {
    loading.value = true
    error.value = null
    
    try {
      // Use the fetchMeetingAudioFiles from useAudioFiles hook
      const data = await fetchMeetingAudioFiles(meetingId)
      meetingAudioFiles.value = data
      return data
    } catch (err: any) {
      console.error('Error fetching meeting audio files:', err)
      error.value = err.message || 'Failed to fetch meeting audio files'
      return []
    } finally {
      loading.value = false
    }
  }

  // Get audio files for a meeting directly (alternative method)
  const fetchAudioByMeetingId = async (meetingId: string, showLoading: boolean = true) => {
    if (showLoading) {
      loading.value = true
    }
    error.value = null
    
    try {
      const url = `${API_URL}/meetings/${meetingId}/audio-files`
      
      const response = await fetch(url)
      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}))
        throw new Error(errorData.detail || `Request failed with status ${response.status}`)
      }
      
      const data = await response.json()
      meetingAudioFiles.value = data
      return data
    } catch (err: any) {
      console.error('Error fetching audio files for meeting:', err)
      error.value = err.message || 'Failed to fetch audio files for meeting'
      return []
    } finally {
      if (showLoading) {
        loading.value = false
      }
    }
  }

  return {
    meetings,
    currentMeeting,
    meetingAudioFiles,
    loading,
    error,
    fetchMeetings,
    fetchMeeting,
    createMeeting,
    updateMeeting,
    deleteMeeting,
    clearMeetingTranscriptAndSummary,
    getMeetingAudioFiles,
    fetchAudioByMeetingId
  }
}
