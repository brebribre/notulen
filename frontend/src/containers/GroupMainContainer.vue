<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useRoute } from 'vue-router'
import { useGroups } from '@/hooks/useGroups'
import { Button } from '@/components/ui/button'
import { Separator } from '@/components/ui/separator'
import { 
  Dialog, 
  DialogTrigger, 
  DialogContent, 
  DialogHeader, 
  DialogTitle, 
  DialogDescription, 
  DialogFooter
} from '@/components/ui/dialog'
import { Input } from '@/components/ui/input'
import { Users, User, Loader2, Settings, Pencil, UserPlus, Trash, RefreshCw, X } from 'lucide-vue-next'

const route = useRoute()
const groupId = computed(() => route.params.groupId as string)

const { 
  currentGroup, 
  groupMembers, 
  loading,
  error,
  fetchGroup,
  fetchGroupMembers,
  updateGroup,
  removeUserFromGroup,
  addUserToGroup,
  userId,
  searchUsers
} = useGroups()

// State for editing group
const isEditing = ref(false)
const editName = ref('')
const editDescription = ref('')
const loadingEdit = ref(false)

// State for adding members
const showAddMemberDialog = ref(false)
const newMemberEmail = ref('')
const searchResults = ref<any[]>([])
const selectedUser = ref<any>(null)
const searchLoading = ref(false)
const loadingAddMember = ref(false)

// Active section
const activeSection = ref('details')

// State for members list
const membersLoading = ref(false)
const membersError = ref<string | null>(null)

// Fetch group data on mount
onMounted(async () => {
  if (groupId.value) {
    await fetchGroup(groupId.value)
    await loadGroupMembers()
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

// Search for users
const searchForUsers = async () => {
  if (!newMemberEmail.value || newMemberEmail.value.length < 2) {
    searchResults.value = []
    return
  }
  
  searchLoading.value = true
  try {
    searchResults.value = await searchUsers(newMemberEmail.value)
  } finally {
    searchLoading.value = false
  }
}

// Add new member
const addMember = async () => {
  if (!selectedUser.value) return
  
  loadingAddMember.value = true
  try {
    // Add the selected user to the group
    const userToAdd = {
      user_id: selectedUser.value.id,
      group_id: groupId.value,
      role: 'member'
    }
    
    await addUserToGroup(groupId.value, userToAdd)
    resetMemberForm()
  } catch (err) {
    error.value = `Failed to add member: ${err instanceof Error ? err.message : String(err)}`
  } finally {
    loadingAddMember.value = false
  }
}

// Reset member form
const resetMemberForm = () => {
  newMemberEmail.value = ''
  selectedUser.value = null
  searchResults.value = []
  showAddMemberDialog.value = false
}

// Select user from search results
const selectUser = (user: any) => {
  selectedUser.value = user
  newMemberEmail.value = user.email
  searchResults.value = []
}

// Remove member
const removeMember = async (memberId: string) => {
  await removeUserFromGroup(groupId.value, memberId)
}

// Check if current user is admin
const isUserAdmin = computed(() => {
  if (!groupMembers.value.length || !userId.value) return false
  
  const currentUserMembership = groupMembers.value.find(
    member => member.user_id === userId.value
  )
  
  return currentUserMembership?.role === 'admin'
})

// Fetch group members
const loadGroupMembers = async () => {
  membersLoading.value = true
  membersError.value = null
  
  try {
    await fetchGroupMembers(groupId.value)
  } catch (err) {
    membersError.value = `Failed to load members: ${err instanceof Error ? err.message : String(err)}`
  } finally {
    membersLoading.value = false
  }
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
            Members ({{ groupMembers.length }})
          </div>
        </button>
      </div>
      
      <!-- Details Section -->
      <div v-if="activeSection === 'details'" class="space-y-4">
        <div class="space-y-2">
          <h2 class="text-xl font-semibold">Group Information</h2>
          <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div class="p-4 border rounded-lg">
              <h3 class="font-medium">Group ID</h3>
              <p class="text-muted-foreground font-mono text-sm mt-1">{{ groupId }}</p>
            </div>
            <div class="p-4 border rounded-lg">
              <h3 class="font-medium">Created By</h3>
              <p class="text-muted-foreground mt-1">{{ currentGroup.created_by }}</p>
            </div>
          </div>
        </div>
      </div>
      
      <!-- Members Section -->
      <div v-if="activeSection === 'members'" class="space-y-4">
        <div class="flex justify-between items-center">
          <h2 class="text-xl font-semibold">Group Members</h2>
          
          <!-- Add Member Dialog -->
          <Dialog v-model:open="showAddMemberDialog">
            <DialogTrigger asChild>
              <Button v-if="isUserAdmin" size="sm">
                <UserPlus class="mr-1 h-4 w-4" />
                Add Member
              </Button>
            </DialogTrigger>
            
            <DialogContent class="sm:max-w-[425px]">
              <DialogHeader>
                <DialogTitle>Add Member</DialogTitle>
                <DialogDescription>
                  Enter the email or name of the user you want to add to this group.
                </DialogDescription>
              </DialogHeader>
              
              <div class="space-y-4 py-4">
                <div class="space-y-2">
                  <label class="text-sm font-medium leading-none" for="email">Search Users</label>
                  <div class="relative">
                    <Input 
                      id="email"
                      v-model="newMemberEmail" 
                      type="text" 
                      placeholder="Enter email or name"
                      @input="searchForUsers"
                    />
                    <Loader2 
                      v-if="searchLoading" 
                      class="absolute right-2 top-2 h-4 w-4 animate-spin text-muted-foreground"
                    />
                  </div>
                </div>
                
                <!-- Search Results -->
                <div v-if="searchResults.length > 0" class="border rounded-md max-h-40 overflow-y-auto">
                  <div 
                    v-for="user in searchResults" 
                    :key="user.id"
                    class="p-2 hover:bg-accent cursor-pointer border-b last:border-b-0"
                    @click="selectUser(user)"
                  >
                    <div class="font-medium">{{ user.name || 'Unnamed User' }}</div>
                    <div class="text-xs text-muted-foreground">{{ user.email }}</div>
                  </div>
                </div>
                
                <!-- Selected User -->
                <div v-if="selectedUser" class="bg-primary/10 p-3 rounded-md">
                  <div class="flex items-center justify-between">
                    <div>
                      <div class="font-medium">{{ selectedUser.name || 'Unnamed User' }}</div>
                      <div class="text-xs text-muted-foreground">{{ selectedUser.email }}</div>
                    </div>
                    <Button 
                      variant="ghost" 
                      size="icon" 
                      @click="selectedUser = null"
                      class="h-6 w-6"
                    >
                      <X class="h-4 w-4" />
                    </Button>
                  </div>
                </div>
                
                <DialogFooter class="mt-6">
                  <Button 
                    variant="outline" 
                    type="button"
                    @click="resetMemberForm"
                  >
                    Cancel
                  </Button>
                  <Button 
                    type="button" 
                    @click="addMember"
                    :disabled="loadingAddMember || !selectedUser"
                  >
                    <Loader2 v-if="loadingAddMember" class="mr-1 h-4 w-4 animate-spin" />
                    {{ loadingAddMember ? 'Adding...' : 'Add Member' }}
                  </Button>
                </DialogFooter>
              </div>
            </DialogContent>
          </Dialog>
        </div>
        
        <!-- Members Loading State -->
        <div v-if="membersLoading" class="flex justify-center py-8">
          <div class="flex flex-col items-center space-y-2">
            <Loader2 class="h-6 w-6 animate-spin text-primary" />
            <span class="text-sm text-muted-foreground">Loading members...</span>
          </div>
        </div>
        
        <!-- Members Error State -->
        <div v-else-if="membersError" class="p-4 bg-destructive/10 text-destructive rounded-lg">
          <p>{{ membersError }}</p>
          <Button 
            @click="loadGroupMembers" 
            variant="outline"
            size="sm"
            class="mt-2"
          >
            <RefreshCw class="mr-1 h-4 w-4" />
            Retry
          </Button>
        </div>
        
        <!-- Members List -->
        <div v-else class="space-y-2">
          <div 
            v-for="member in groupMembers" 
            :key="member.user_id"
            class="flex items-center justify-between p-3 border rounded-lg hover:bg-accent/50 transition-colors"
          >
            <div class="flex items-center space-x-3">
              <div class="bg-muted rounded-full p-2">
                <User class="h-5 w-5 text-muted-foreground" />
              </div>
              <div>
                <div class="font-medium">{{ member.name || 'Unnamed User' }}</div>
                <div class="text-sm text-muted-foreground">{{ member.email }}</div>
              </div>
              <div class="text-xs bg-primary/10 text-primary px-2 py-1 rounded-full">
                {{ member.role }}
              </div>
            </div>
            
            <!-- Admin actions -->
            <div class="flex items-center space-x-2">
              <span v-if="member.user_id === userId" class="text-xs text-muted-foreground mr-2">(You)</span>
              
              <Button 
                v-if="isUserAdmin && member.user_id !== userId"
                @click="removeMember(member.user_id)"
                variant="ghost" 
                size="sm"
              >
                <Trash class="h-4 w-4 text-destructive" />
              </Button>
            </div>
          </div>
          
          <div v-if="groupMembers.length === 0" class="text-center p-8 text-muted-foreground">
            <div class="mb-2 flex justify-center">
              <Users class="h-10 w-10 text-muted-foreground/50" />
            </div>
            <h3 class="text-lg font-medium mb-1">No members found</h3>
            <p class="text-sm">This group doesn't have any members yet.</p>
          </div>
        </div>
      </div>
    </div>
    
    <!-- Group not found -->
    <div v-else class="text-center p-8">
      <h1 class="text-2xl font-bold mb-2">Group Not Found</h1>
      <p class="text-muted-foreground mb-4">The group you are looking for does not exist or you do not have access to it.</p>
      <Button @click="$router.push('/dashboard')">Return to Dashboard</Button>
    </div>
  </div>
</template>
