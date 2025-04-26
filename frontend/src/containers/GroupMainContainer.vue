<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useRoute } from 'vue-router'
import { useGroups } from '@/hooks/useGroups'
import { useAgents } from '@/hooks/useAgents'
import { Button } from '@/components/ui/button'
import { Separator } from '@/components/ui/separator'
import { Input } from '@/components/ui/input'
import { Users, Loader2, Settings, Pencil, FileAudio, Bot, Send, X } from 'lucide-vue-next'
import MembersContainer from '@/containers/MembersContainer.vue'
import DetailsContainer from '@/containers/DetailsContainer.vue'
import AudioContainer from '@/containers/AudioContainer.vue'
import { 
  Sheet, 
  SheetContent, 
  SheetDescription, 
  SheetFooter, 
  SheetHeader, 
  SheetTitle 
} from '@/components/ui/sheet'

const route = useRoute()
const groupId = computed(() => route.params.groupId as string)

const { 
  currentGroup, 
  groupMembers, 
  loading,
  error,
  fetchGroup,
  updateGroup,
  userId,
} = useGroups()

const {
  loading: agentLoading,
  error: agentError,
  getGroupAssistantResponse
} = useAgents()

// State for editing group
const isEditing = ref(false)
const editName = ref('')
const editDescription = ref('')
const loadingEdit = ref(false)

// Active section
const activeSection = ref('details')

// Chat state
const isChatOpen = ref(false)
const chatMessage = ref('')
const chatMessages = ref([
  { role: 'system', content: 'Hello! I am your group assistant. How can I help you today?' }
])
const isSendingMessage = ref(false)

// Fetch group data on mount
onMounted(async () => {
  if (groupId.value) {
    await fetchGroup(groupId.value)
  }
})

// Start editing group
const startEditing = () => {
  if (!currentGroup.value) return
  
  editName.value = currentGroup.value.name
  editDescription.value = currentGroup.value.description || ''
  isEditing.value = true
}

// Save group edits
const saveGroupEdits = async () => {
  if (!currentGroup.value || !editName.value.trim()) return
  
  loadingEdit.value = true
  try {
    await updateGroup(groupId.value, {
      name: editName.value,
      description: editDescription.value || undefined
    })
    isEditing.value = false
  } finally {
    loadingEdit.value = false
  }
}

// Cancel editing
const cancelEditing = () => {
  isEditing.value = false
}

// Check if current user is admin
const isUserAdmin = computed(() => {
  if (!groupMembers.value.length || !userId.value) return false
  
  const currentUserMembership = groupMembers.value.find(
    member => member.user_id === userId.value
  )
  
  return currentUserMembership?.role === 'admin'
})

// Handle errors from child components
const handleError = (errorMessage: string) => {
  error.value = errorMessage
}

// Chat functions
const sendMessage = async () => {
  if (!chatMessage.value.trim()) return
  
  // Add user message
  const userMessage = {
    role: 'user',
    content: chatMessage.value
  }
  chatMessages.value.push(userMessage)
  
  // Clear input
  const userQuery = chatMessage.value
  chatMessage.value = ''
  
  // Show typing indicator
  isSendingMessage.value = true
  
  try {
    // Prepare all messages for context
    const messages = [...chatMessages.value]
    
    // Call the agent API
    const response = await getGroupAssistantResponse(messages, groupId.value)
    
    if (response) {
      // Add agent response to chat
      chatMessages.value.push({
        role: 'system',
        content: response
      })
    } else {
      // Handle error
      chatMessages.value.push({
        role: 'system',
        content: "I'm sorry, I encountered an error processing your request. Please try again."
      })
    }
  } catch (err) {
    console.error('Error sending message to agent:', err)
    chatMessages.value.push({
      role: 'system',
      content: "I'm sorry, I encountered an error processing your request. Please try again."
    })
  } finally {
    isSendingMessage.value = false
  }
}

// Clear chat history
const clearChat = () => {
  chatMessages.value = [
    { role: 'system', content: 'Hello! I am your group assistant. How can I help you today?' }
  ]
}
</script>

<template>
  <div class="container p-4 mx-auto">
    <!-- Loading state -->
    <div v-if="loading" class="flex flex-col items-center justify-center my-12 space-y-4">
      <Loader2 class="h-8 w-8 animate-spin text-primary" />
      <p class="text-muted-foreground">Loading group details...</p>
    </div>
    
    <!-- Error state -->
    <div v-else-if="error" class="p-4 bg-destructive/10 text-destructive rounded-lg">
      <p>{{ error }}</p>
      <Button 
        @click="fetchGroup(groupId)" 
        variant="outline"
        size="sm"
        class="mt-2"
      >
        Try again
      </Button>
    </div>
    
    <!-- Group details -->
    <div v-else-if="currentGroup" class="space-y-8">
      <!-- Group header -->
      <div class="relative space-y-4">
        <div class="flex justify-between items-start">
          <div>
            <div v-if="!isEditing" class="space-y-1">
              <h1 class="text-3xl font-bold">{{ currentGroup.name }}</h1>
              <p v-if="currentGroup.description" class="text-muted-foreground">
                {{ currentGroup.description }}
              </p>
              <p v-else class="text-muted-foreground italic">No description</p>
            </div>
            
            <!-- Edit form -->
            <div v-else class="space-y-3">
              <Input
                v-model="editName"
                class="text-xl font-semibold"
                placeholder="Group name"
              />
              <textarea
                v-model="editDescription"
                class="w-full h-20 rounded-md border border-input bg-transparent p-2 text-sm"
                placeholder="Group description (optional)"
              />
              <div class="flex space-x-2">
                <Button
                  @click="saveGroupEdits"
                  :disabled="loadingEdit || !editName.trim()"
                >
                  <Loader2 v-if="loadingEdit" class="mr-1 h-4 w-4 animate-spin" />
                  Save
                </Button>
                <Button @click="cancelEditing" variant="outline">Cancel</Button>
              </div>
            </div>
          </div>
          
          <!-- Action buttons -->
          <div v-if="!isEditing && isUserAdmin" class="flex space-x-2">
            <Button @click="startEditing" variant="outline" size="sm">
              <Pencil class="mr-1 h-4 w-4" />
              Edit
            </Button>
          </div>
        </div>
        
        <div class="text-sm text-muted-foreground">
          Created: {{ new Date(currentGroup.created_at).toLocaleDateString() }}
        </div>
        
        <Separator />
      </div>
      
      <!-- Section Navigation -->
      <div class="flex border-b space-x-1">
        <button 
          @click="activeSection = 'details'" 
          class="px-4 py-2 border-b-2 font-medium text-sm"
          :class="activeSection === 'details' 
            ? 'border-primary text-primary' 
            : 'border-transparent text-muted-foreground hover:text-foreground'"
        >
          <div class="flex items-center">
            <Settings class="mr-1 h-4 w-4" />
            Details
          </div>
        </button>
        
        <button 
          @click="activeSection = 'members'" 
          class="px-4 py-2 border-b-2 font-medium text-sm"
          :class="activeSection === 'members' 
            ? 'border-primary text-primary' 
            : 'border-transparent text-muted-foreground hover:text-foreground'"
        >
          <div class="flex items-center">
            <Users class="mr-1 h-4 w-4" />
            Members
          </div>
        </button>
        
        <button 
          @click="activeSection = 'audio'" 
          class="px-4 py-2 border-b-2 font-medium text-sm"
          :class="activeSection === 'audio' 
            ? 'border-primary text-primary' 
            : 'border-transparent text-muted-foreground hover:text-foreground'"
        >
          <div class="flex items-center">
            <FileAudio class="mr-1 h-4 w-4" />
            Audio
          </div>
        </button>
      </div>
      
      <!-- Details Section -->
      <DetailsContainer
        v-if="activeSection === 'details'"
        :groupId="groupId"
        :currentGroup="currentGroup"
      />
      
      <!-- Members Section -->
      <MembersContainer 
        v-if="activeSection === 'members'"
        :groupId="groupId"
        @error="handleError"
      />
      
      <!-- Audio Section -->
      <AudioContainer
        v-if="activeSection === 'audio'"
        :groupId="groupId"
        @error="handleError"
      />
    </div>
    
    <!-- Group not found -->
    <div v-else class="text-center p-8">
      <h1 class="text-2xl font-bold mb-2">Group Not Found</h1>
      <p class="text-muted-foreground mb-4">The group you are looking for does not exist or you do not have access to it.</p>
      <Button @click="$router.push('/dashboard')">Return to Dashboard</Button>
    </div>
    
    <!-- Chatbot Button -->
    <Button 
      @click="isChatOpen = true"
      class="fixed bottom-6 right-6 h-14 w-14 rounded-full shadow-lg"
      size="icon"
    >
      <Bot class="h-6 w-6" />
    </Button>
    
    <!-- Chat Sheet -->
    <Sheet :open="isChatOpen" @update:open="isChatOpen = $event">
      <SheetContent class="w-[90vw] sm:max-w-[450px] flex flex-col h-full p-0">
        <SheetHeader class="px-6 pt-6 pb-2">
          <SheetTitle>Group Assistant</SheetTitle>
          <SheetDescription>
            Ask questions about your group or meetings
          </SheetDescription>
          <Button 
            @click="clearChat" 
            variant="ghost" 
            size="sm"
            class="absolute right-12 top-4"
          >
            <X class="h-4 w-4 mr-1" />
            Clear
          </Button>
        </SheetHeader>
        
        <!-- Chat Messages -->
        <div class="flex-1 overflow-y-auto px-6 py-4 bg-muted/30">
          <div class="space-y-4">
            <div 
              v-for="(message, index) in chatMessages" 
              :key="index"
              :class="[
                'flex',
                message.role === 'user' ? 'justify-end' : 'justify-start'
              ]"
            >
              <div 
                :class="[
                  'max-w-[80%] rounded-lg px-4 py-2',
                  message.role === 'user' 
                    ? 'bg-primary text-primary-foreground' 
                    : 'bg-muted'
                ]"
              >
                <p class="text-sm whitespace-pre-line">{{ message.content }}</p>
              </div>
            </div>
            
            <!-- Typing indicator -->
            <div v-if="isSendingMessage" class="flex justify-start">
              <div class="bg-muted rounded-lg px-4 py-2">
                <p class="text-sm flex items-center gap-1">
                  <span class="animate-bounce">•</span>
                  <span class="animate-bounce delay-100">•</span>
                  <span class="animate-bounce delay-200">•</span>
                </p>
              </div>
            </div>
            
            <!-- Agent error message -->
            <div v-if="agentError" class="bg-destructive/10 text-destructive p-2 rounded-md text-sm">
              {{ agentError }}
            </div>
          </div>
        </div>
        
        <!-- Input Area -->
        <div class="p-4 border-t">
          <form @submit.prevent="sendMessage" class="flex gap-2">
            <Input
              v-model="chatMessage"
              placeholder="Type your message..."
              class="flex-1"
              :disabled="isSendingMessage"
            />
            <Button type="submit" :disabled="!chatMessage.trim() || isSendingMessage">
              <Send class="h-4 w-4" />
            </Button>
          </form>
        </div>
      </SheetContent>
    </Sheet>
  </div>
</template>
