<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useGroups } from '@/hooks/useGroups'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Skeleton } from '@/components/ui/skeleton'
import { Separator } from '@/components/ui/separator'
import { 
  Dialog,
  DialogTrigger,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
  DialogClose
} from '@/components/ui/dialog'
import { AlertDialog, AlertDialogContent, AlertDialogHeader, AlertDialogFooter, 
  AlertDialogTitle, AlertDialogDescription, AlertDialogCancel, AlertDialogAction 
} from '@/components/ui/alert-dialog'
import { Plus, Loader2, RefreshCw, User, Trash2 } from 'lucide-vue-next'

// Get groups functionality from the hook
const { 
  groups, 
  loading, 
  error, 
  fetchGroups, 
  createGroup,
  deleteGroup
} = useGroups()

// State for the new group form
const newGroupName = ref('')
const newGroupDescription = ref('')
const creatingGroup = ref(false)
const dialogOpen = ref(false)

// State for delete confirmation
const deleteDialogOpen = ref(false)
const groupToDelete = ref<{ id: string, name: string } | null>(null)
const deletingGroup = ref(false)

// Fetch groups when component mounts
onMounted(async () => {
  await fetchGroups(true) // true to filter by current user
})

// Handle form submission for creating a new group
const handleCreateGroup = async () => {
  if (!newGroupName.value.trim()) return
  
  creatingGroup.value = true
  try {
    await createGroup(newGroupName.value, newGroupDescription.value)
    // Reset form
    newGroupName.value = ''
    newGroupDescription.value = ''
    dialogOpen.value = false
  } finally {
    creatingGroup.value = false
  }
}

// Function to show delete confirmation dialog
const confirmDeleteGroup = (groupId: string, groupName: string) => {
  groupToDelete.value = { id: groupId, name: groupName }
  deleteDialogOpen.value = true
}

// Function to handle group deletion
const handleDeleteGroup = async () => {
  if (!groupToDelete.value) return
  
  deletingGroup.value = true
  try {
    await deleteGroup(groupToDelete.value.id)
    deleteDialogOpen.value = false
    groupToDelete.value = null
  } catch (err) {
    console.error('Error deleting group:', err)
  } finally {
    deletingGroup.value = false
  }
}

// Reset form when dialog closes
const onDialogOpenChange = (open: boolean) => {
  dialogOpen.value = open
  if (!open) {
    newGroupName.value = ''
    newGroupDescription.value = ''
  }
}
</script>

<template>
  <div class="container mx-auto p-6">
    <div class="flex justify-between items-center mb-6">
      <h1 class="text-2xl font-bold">My Groups</h1>
      
      <Dialog v-model:open="dialogOpen" @update:open="onDialogOpenChange">
        <DialogTrigger as-child>
          <Button>
            <Plus class="mr-1 h-4 w-4" />
            New Group
          </Button>
        </DialogTrigger>
        
        <DialogContent class="sm:max-w-[425px]">
          <DialogHeader>
            <DialogTitle>Create New Group</DialogTitle>
            <DialogDescription>
              Create a new group to collaborate with others. Enter the details below.
            </DialogDescription>
          </DialogHeader>
          
          <form @submit.prevent="handleCreateGroup" class="space-y-4 py-4">
            <div class="space-y-2">
              <label class="text-sm font-medium leading-none" for="name">Group Name</label>
              <Input 
                id="name"
                v-model="newGroupName" 
                type="text" 
                required
                placeholder="Enter group name"
              />
            </div>
            
            <div class="space-y-2">
              <label class="text-sm font-medium leading-none" for="description">Description (optional)</label>
              <textarea 
                id="description"
                v-model="newGroupDescription" 
                class="flex w-full rounded-md border border-input bg-transparent px-3 py-2 text-sm shadow-sm placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring"
                rows="3"
                placeholder="Describe the purpose of this group"
              ></textarea>
            </div>
            
            <DialogFooter class="mt-6">
              <DialogClose asChild>
                <Button variant="outline" type="button">Cancel</Button>
              </DialogClose>
              <Button 
                type="submit" 
                :disabled="creatingGroup || !newGroupName.trim()"
              >
                <Loader2 v-if="creatingGroup" class="mr-1 h-4 w-4 animate-spin" />
                {{ creatingGroup ? 'Creating...' : 'Create Group' }}
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>
    </div>
    
    <!-- Loading State -->
    <div v-if="loading" class="flex flex-col items-center justify-center my-12 space-y-4">
      <Loader2 class="h-8 w-8 animate-spin text-primary" />
      <p class="text-muted-foreground">Loading your groups...</p>
    </div>
    
    <!-- Error State -->
    <div v-else-if="error" class="p-4 bg-destructive/10 text-destructive rounded-lg mb-4">
      <p>{{ error }}</p>
      <Button 
        @click="fetchGroups()" 
        variant="outline"
        size="sm"
        class="mt-2"
      >
        <RefreshCw class="mr-1" />
        Try again
      </Button>
    </div>
    
    <!-- Groups List -->
    <div v-else-if="groups.length > 0" class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
      <div 
        v-for="group in groups" 
        :key="group.id" 
        class="bg-card border rounded-lg overflow-hidden hover:shadow-md transition"
      >
        <div class="p-4">
          <h2 class="text-xl font-semibold mb-2">{{ group.name }}</h2>
          <p v-if="group.description" class="text-muted-foreground mb-4">{{ group.description }}</p>
          <p v-else class="text-muted-foreground italic mb-4">No description</p>
          
          <Separator class="my-3" />
          
          <div class="flex justify-between items-center text-sm text-muted-foreground">
            <span>Created: {{ new Date(group.created_at).toLocaleDateString() }}</span>
            <div class="flex gap-2">
              <Button 
                variant="destructive"
                size="sm"
                @click="confirmDeleteGroup(group.id, group.name)"
              >
                <Trash2 class="h-4 w-4" />
              </Button>
              <Button 
                size="sm"
                @click="$router.push(`/groups/${group.id}`)"
              >
                View Details
              </Button>
            </div>
          </div>
        </div>
      </div>
    </div>
    
    <!-- Empty State -->
    <div v-else class="text-center py-16 max-w-md mx-auto">
      <div class="bg-muted rounded-full p-4 w-16 h-16 flex items-center justify-center mx-auto mb-4">
        <User class="h-8 w-8 text-muted-foreground" />
      </div>
      <h3 class="text-xl font-medium mb-2">No Groups Yet</h3>
      <p class="text-muted-foreground mb-6">Create your first group to get started with collaboration</p>
      <Button 
        @click="dialogOpen = true" 
        size="lg"
      >
        <Plus class="mr-1" />
        Create a Group
      </Button>
    </div>
    
    <!-- Delete Confirmation Dialog -->
    <AlertDialog v-model:open="deleteDialogOpen">
      <AlertDialogContent>
        <AlertDialogHeader>
          <AlertDialogTitle>Are you sure you want to delete this group?</AlertDialogTitle>
          <AlertDialogDescription>
            This will permanently delete the group "{{ groupToDelete?.name }}" and all associated data. 
            This action cannot be undone.
          </AlertDialogDescription>
        </AlertDialogHeader>
        <AlertDialogFooter>
          <AlertDialogCancel>Cancel</AlertDialogCancel>
          <AlertDialogAction 
            @click="handleDeleteGroup" 
            class="bg-destructive text-destructive-foreground hover:bg-destructive/90"
            :disabled="deletingGroup"
          >
            <Loader2 v-if="deletingGroup" class="mr-1 h-4 w-4 animate-spin" />
            {{ deletingGroup ? 'Deleting...' : 'Delete Group' }}
          </AlertDialogAction>
        </AlertDialogFooter>
      </AlertDialogContent>
    </AlertDialog>
    
    <!-- Skeleton Loading State (not shown currently but available for future use) -->
    <div v-if="false" class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
      <div v-for="i in 3" :key="i" class="border rounded-lg p-4">
        <Skeleton class="h-6 w-3/4 mb-2" />
        <Skeleton class="h-4 w-full mb-1" />
        <Skeleton class="h-4 w-2/3 mb-4" />
        <div class="flex justify-between items-center pt-3">
          <Skeleton class="h-4 w-1/3" />
          <Skeleton class="h-8 w-24" />
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
/* Additional styles if needed */
</style>
