import { ref, computed } from 'vue'
import { useAuthStore } from '@/stores/auth'

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

export function useAudioFiles() {
  const authStore = useAuthStore()
  const audioFiles = ref<AudioFile[]>([])
  const currentFile = ref<AudioFile | null>(null)
  const loading = ref(false)
  const error = ref<string | null>(null)

  const API_URL = import.meta.env.VITE_API_URL || ''
  
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

  // Get audio files for a group
  const fetchAudioFiles = async (groupId: string) => {
    loading.value = true
    error.value = null
    
    try {
      const url = `${API_URL}/audio-files`
      const params = { group_id: groupId }
      
      const data = await apiRequest<AudioFile[]>(url, 'GET', undefined, params)
      audioFiles.value = data
      return data
    } catch (err: any) {
      console.error('Error fetching audio files:', err)
      error.value = err.message || 'Failed to fetch audio files'
      return []
    } finally {
      loading.value = false
    }
  }

  // Get a specific audio file by ID
  const fetchAudioFile = async (fileId: string) => {
    loading.value = true
    error.value = null
    
    try {
      const data = await apiRequest<AudioFile>(`${API_URL}/audio-files/${fileId}`, 'GET')
      currentFile.value = data
      return data
    } catch (err: any) {
      console.error('Error fetching audio file:', err)
      error.value = err.message || 'Failed to fetch audio file'
      return null
    } finally {
      loading.value = false
    }
  }

  // Update an audio file
  const updateAudioFile = async (
    fileId: string, 
    data: { 
      original_filename?: string; 
      meeting_datetime?: string;
      meeting_id?: string;
    }
  ) => {
    loading.value = true
    error.value = null
    
    try {
      const updatedFile = await apiRequest<AudioFile>(
        `${API_URL}/audio-files/${fileId}`, 
        'PUT', 
        data
      )
      
      // Update local state if this is the current file
      if (currentFile.value && currentFile.value.id === fileId) {
        currentFile.value = updatedFile
      }
      
      // Update the files list if needed
      const index = audioFiles.value.findIndex(f => f.id === fileId)
      if (index !== -1) {
        audioFiles.value[index] = updatedFile
      }
      
      return updatedFile
    } catch (err: any) {
      console.error('Error updating audio file:', err)
      error.value = err.message || 'Failed to update audio file'
      return null
    } finally {
      loading.value = false
    }
  }

  // Delete an audio file
  const deleteAudioFile = async (fileId: string) => {
    loading.value = true
    error.value = null
    
    try {
      const data = await apiRequest<{ success: boolean; message: string }>(
        `${API_URL}/audio-files/${fileId}`, 
        'DELETE'
      )
      
      // Update local state
      if (currentFile.value && currentFile.value.id === fileId) {
        currentFile.value = null
      }
      
      // Update the files list
      audioFiles.value = audioFiles.value.filter(file => file.id !== fileId)
      
      return data
    } catch (err: any) {
      console.error('Error deleting audio file:', err)
      error.value = err.message || 'Failed to delete audio file'
      return null
    } finally {
      loading.value = false
    }
  }

  // Upload an audio file
  const uploadAudioFile = async (
    file: File, 
    groupId: string, 
    meetingDatetime?: string,
    meetingId?: string
  ) => {
    loading.value = true
    error.value = null
    
    try {
      const formData = new FormData()
      formData.append('file', file)
      formData.append('group_id', groupId)
      
      if (meetingDatetime) {
        formData.append('meeting_datetime', meetingDatetime)
      }
      
      if (meetingId) {
        formData.append('meeting_id', meetingId)
      }
      
      const response = await fetch(`${API_URL}/upload-audio`, {
        method: 'POST',
        body: formData
      })
      
      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}))
        throw new Error(errorData.detail || `Upload failed with status ${response.status}`)
      }
      
      const data = await response.json()
      
      // Refresh the files list
      await fetchAudioFiles(groupId)
      
      return data
    } catch (err: any) {
      console.error('Error uploading audio file:', err)
      error.value = err.message || 'Failed to upload audio file'
      return null
    } finally {
      loading.value = false
    }
  }

  // Get a download URL for an audio file
  const getAudioFileUrl = async (fileId: string) => {
    error.value = null
    
    try {
      const data = await apiRequest<{ url: string }>(
        `${API_URL}/audio-files/${fileId}/download-url`, 
        'GET'
      )
      
      return data.url
    } catch (err: any) {
      console.error('Error getting audio file URL:', err)
      error.value = err.message || 'Failed to get audio file URL'
      return null
    }
  }

  // Format file size helper
  const formatFileSize = (bytes: number | null | undefined) => {
    if (bytes === null || bytes === undefined) return 'Unknown size'
    if (bytes < 1024) return bytes + ' bytes'
    else if (bytes < 1048576) return (bytes / 1024).toFixed(1) + ' KB'
    else return (bytes / 1048576).toFixed(1) + ' MB'
  }

  // Assign an audio file to a meeting
  const assignAudioToMeeting = async (fileId: string, meetingId: string) => {
    loading.value = true
    error.value = null
    
    try {
      const updatedFile = await apiRequest<AudioFile>(
        `${API_URL}/audio-files/${fileId}/assign-to-meeting`, 
        'POST', 
        { meeting_id: meetingId }
      )
      
      // Update local state if this is the current file
      if (currentFile.value && currentFile.value.id === fileId) {
        currentFile.value = updatedFile
      }
      
      // Update the files list if needed
      const index = audioFiles.value.findIndex(f => f.id === fileId)
      if (index !== -1) {
        audioFiles.value[index] = updatedFile
        // Create a new array to trigger reactivity
        audioFiles.value = [...audioFiles.value]
      }
      
      return updatedFile
    } catch (err: any) {
      console.error('Error assigning audio file to meeting:', err)
      error.value = err.message || 'Failed to assign audio file to meeting'
      return null
    } finally {
      loading.value = false
    }
  }

  // Get audio files for a meeting
  const fetchMeetingAudioFiles = async (meetingId: string) => {
    loading.value = true
    error.value = null
    
    try {
      const url = `${API_URL}/meetings/${meetingId}/audio-files`
      
      const data = await apiRequest<AudioFile[]>(url, 'GET')
      audioFiles.value = data
      return data
    } catch (err: any) {
      console.error('Error fetching meeting audio files:', err)
      error.value = err.message || 'Failed to fetch meeting audio files'
      return []
    } finally {
      loading.value = false
    }
  }

  // Get audio files for a meeting using query parameters (alternate method)
  const fetchAudioFilesByMeeting = async (meetingId: string) => {
    loading.value = true
    error.value = null
    
    try {
      const url = `${API_URL}/audio-files/by-meeting`
      const params = { meeting_id: meetingId }
      
      const data = await apiRequest<AudioFile[]>(url, 'GET', undefined, params)
      audioFiles.value = data
      return data
    } catch (err: any) {
      console.error('Error fetching audio files by meeting:', err)
      error.value = err.message || 'Failed to fetch audio files by meeting'
      return []
    } finally {
      loading.value = false
    }
  }

  return {
    audioFiles,
    currentFile,
    loading,
    error,
    
    fetchAudioFiles,
    fetchAudioFile,
    updateAudioFile,
    deleteAudioFile,
    uploadAudioFile,
    getAudioFileUrl,
    formatFileSize,
    assignAudioToMeeting,
    fetchMeetingAudioFiles,
    fetchAudioFilesByMeeting
  }
} 