import { ref } from 'vue'

interface Message {
  role: string
  content: string
}


interface AgentRequestOptions {
  name: string
  instructions: string
  input: string | Message[]
  model?: string
  temperature?: number
  tools?: string[]
}

export function useAgents() {
  const loading = ref(false)
  const error = ref<string | null>(null)

  const API_URL = import.meta.env.VITE_API_URL || ''
  
  // Helper function for API requests
  const apiRequest = async <T>(
    url: string, 
    method: string = 'GET', 
    body?: any
  ): Promise<T> => {
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

  /**
   * Get a response from a single agent
   * This calls the /single-agent-response endpoint
   */
  const getSingleAgentResponse = async (options: AgentRequestOptions) => {
    loading.value = true
    error.value = null
    
    try {
      const url = `${API_URL}/openai/single-agent-response`
      
      // Prepare the request data
      const requestData = {
        name: options.name,
        instructions: options.instructions,
        input: options.input,
        model: options.model || 'gpt-4o',
        temperature: options.temperature || 0.7,
        tools: options.tools || []
      }
      
      const response = await apiRequest<string>(url, 'POST', requestData)
      return response
    } catch (err: any) {
      console.error('Error getting agent response:', err)
      error.value = err.message || 'Failed to get agent response'
      return null
    } finally {
      loading.value = false
    }
  }

  /**
   * Get a response from the group assistant agent
   * This is a convenience wrapper for the getSingleAgentResponse function
   */
  const getGroupAssistantResponse = async (
    input: string | Message[], 
    groupId: string,
    options: {
      model?: string;
      temperature?: number;
      tools?: string[];
    } = {}
  ) => {
    const name = "GroupAssistant"
    const instructions = `You are a helpful assistant for the group with ID ${groupId}.
Your job is to help the users in this group by answering questions about the group,
its meetings, and other relevant information. Be concise, friendly, and helpful.`

    return getSingleAgentResponse({
      name,
      instructions,
      input,
      model: options.model,
      temperature: options.temperature,
      tools: options.tools || ["get_group_meeting_names_and_summaries"]
    })
  }

  return {
    loading,
    error,
    getSingleAgentResponse,
    getGroupAssistantResponse
  }
}
