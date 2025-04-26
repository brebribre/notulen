import { ref, computed } from 'vue'
import { useAuthStore } from '@/stores/auth'

interface Group {
  id: string
  name: string
  description: string | null
  created_at: string
  created_by: string
}

interface GroupMember {
  user_id: string
  role: string
  joined_at: string
  email: string
  name: string | null
}

interface UserGroup {
  user_id: string
  group_id: string
  role?: string
}

export function useGroups() {
  const authStore = useAuthStore()
  const groups = ref<Group[]>([])
  const currentGroup = ref<Group | null>(null)
  const groupMembers = ref<GroupMember[]>([])
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

  // Get all groups or filter by user_id
  const fetchGroups = async (filterByUser = true) => {
    loading.value = true
    error.value = null
    
    try {
      const url = `${API_URL}/groups`
      const params = filterByUser ? { user_id: userId.value } : undefined
      
      const data = await apiRequest<Group[]>(url, 'GET', undefined, params)
      groups.value = data
      return data
    } catch (err: any) {
      console.error('Error fetching groups:', err)
      error.value = err.message || 'Failed to fetch groups'
      return []
    } finally {
      loading.value = false
    }
  }

  // Get a specific group by ID
  const fetchGroup = async (groupId: string) => {
    loading.value = true
    error.value = null
    
    try {
      const data = await apiRequest<Group>(`${API_URL}/groups/${groupId}`, 'GET')
      currentGroup.value = data
      return data
    } catch (err: any) {
      console.error('Error fetching group:', err)
      error.value = err.message || 'Failed to fetch group'
      return null
    } finally {
      loading.value = false
    }
  }

  // Create a new group
  const createGroup = async (name: string, description?: string) => {
    loading.value = true
    error.value = null
    
    try {
      const data = await apiRequest<Group>(
        `${API_URL}/groups`, 
        'POST', 
        { name, description }, 
        { user_id: userId.value }
      )
      
      // Update the groups list
      await fetchGroups()
      
      return data
    } catch (err: any) {
      console.error('Error creating group:', err)
      error.value = err.message || 'Failed to create group'
      return null
    } finally {
      loading.value = false
    }
  }

  // Update a group
  const updateGroup = async (groupId: string, data: { name?: string; description?: string }) => {
    loading.value = true
    error.value = null
    
    try {
      const updatedGroup = await apiRequest<Group>(
        `${API_URL}/groups/${groupId}`, 
        'PUT', 
        data, 
        { user_id: userId.value }
      )
      
      // Update local state
      if (currentGroup.value && currentGroup.value.id === groupId) {
        currentGroup.value = updatedGroup
      }
      
      // Update the groups list
      await fetchGroups()
      
      return updatedGroup
    } catch (err: any) {
      console.error('Error updating group:', err)
      error.value = err.message || 'Failed to update group'
      return null
    } finally {
      loading.value = false
    }
  }

  // Delete a group
  const deleteGroup = async (groupId: string) => {
    loading.value = true
    error.value = null
    
    try {
      const data = await apiRequest<{ success: boolean; message: string }>(
        `${API_URL}/groups/${groupId}`, 
        'DELETE', 
        undefined, 
        { user_id: userId.value }
      )
      
      // Update local state
      if (currentGroup.value && currentGroup.value.id === groupId) {
        currentGroup.value = null
      }
      
      // Update the groups list
      await fetchGroups()
      
      return data
    } catch (err: any) {
      console.error('Error deleting group:', err)
      error.value = err.message || 'Failed to delete group'
      return null
    } finally {
      loading.value = false
    }
  }

  // Get all members of a group
  const fetchGroupMembers = async (groupId: string) => {
    loading.value = true
    error.value = null
    
    try {
      const data = await apiRequest<GroupMember[]>(`${API_URL}/groups/${groupId}/members`, 'GET')
      groupMembers.value = data
      return data
    } catch (err: any) {
      console.error('Error fetching group members:', err)
      error.value = err.message || 'Failed to fetch group members'
      return []
    } finally {
      loading.value = false
    }
  }

  // Add a user to a group
  const addUserToGroup = async (groupId: string, userToAdd: UserGroup) => {
    loading.value = true
    error.value = null
    
    try {
      const data = await apiRequest<{ success: boolean; message: string }>(
        `${API_URL}/groups/${groupId}/members`, 
        'POST', 
        userToAdd, 
        { admin_id: userId.value }
      )
      
      // Refresh the members list
      await fetchGroupMembers(groupId)
      
      return data
    } catch (err: any) {
      console.error('Error adding user to group:', err)
      error.value = err.message || 'Failed to add user to group'
      return null
    } finally {
      loading.value = false
    }
  }

  // Remove a user from a group
  const removeUserFromGroup = async (groupId: string, userIdToRemove: string) => {
    loading.value = true
    error.value = null
    
    try {
      const data = await apiRequest<{ success: boolean; message: string }>(
        `${API_URL}/groups/${groupId}/members/${userIdToRemove}`, 
        'DELETE', 
        undefined, 
        { admin_id: userId.value }
      )
      
      // Refresh the members list
      await fetchGroupMembers(groupId)
      
      return data
    } catch (err: any) {
      console.error('Error removing user from group:', err)
      error.value = err.message || 'Failed to remove user from group'
      return null
    } finally {
      loading.value = false
    }
  }

  // Leave a group (remove yourself)
  const leaveGroup = async (groupId: string) => {
    return removeUserFromGroup(groupId, userId.value)
  }

  return {
    groups,
    currentGroup,
    groupMembers,
    loading,
    error,
    userId,
    
    fetchGroups,
    fetchGroup,
    createGroup,
    updateGroup,
    deleteGroup,
    fetchGroupMembers,
    addUserToGroup,
    removeUserFromGroup,
    leaveGroup
  }
}
