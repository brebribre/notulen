<script setup lang="ts">
import { defineProps, onMounted, ref } from 'vue'
import { Button } from '@/components/ui/button'
import { useRouter } from 'vue-router'
import { useMeetings } from '@/hooks/useMeetings'
import { formatDate } from '@/lib/utils'
import {
  Table,
  TableBody,
  TableCaption,
  TableCell,
  TableEmpty,
  TableHead,
  TableHeader,
  TableRow
} from '@/components/ui/table'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger
} from '@/components/ui/dialog'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Loader2 } from 'lucide-vue-next'

const router = useRouter()
const props = defineProps<{
  groupId: string;
  currentGroup: any;
}>()

const { meetings, loading, error, fetchMeetings, createMeeting } = useMeetings()

// Format date for display
function formatDateTime(dateTimeStr: string) {
  if (!dateTimeStr) return '-'
  return formatDate(new Date(dateTimeStr), 'PPp') // Format: Apr 5, 2023, 1:25 PM
}

// Load meetings when component mounts
onMounted(async () => {
  await fetchMeetings(props.groupId)
})

// New meeting dialog state
const isDialogOpen = ref(false)
const newMeetingName = ref('')
const meetingDate = ref(new Date().toISOString().split('T')[0])
const meetingTime = ref(new Date().toTimeString().slice(0, 5))
const isCreating = ref(false)
const createError = ref('')

// Navigate to record page
const navigateToRecord = () => {
  router.push(`/groups/${props.groupId}/record`)
}

// Navigate to meeting details
const navigateToMeeting = (meetingId: string) => {
  router.push(`/groups/${props.groupId}/meetings/${meetingId}`)
}

// Create a new meeting
const handleCreateMeeting = async () => {
  if (!newMeetingName.value.trim()) {
    createError.value = 'Meeting name is required'
    return
  }

  isCreating.value = true
  createError.value = ''
  
  try {
    // Combine date and time
    const meetingDateTime = new Date(`${meetingDate.value}T${meetingTime.value}:00`)
    
    const meetingData = {
      group_id: props.groupId,
      name: newMeetingName.value.trim(),
      meeting_datetime: meetingDateTime.toISOString()
    }
    
    const result = await createMeeting(meetingData)
    
    if (result) {
      // Close dialog and reset form
      isDialogOpen.value = false
      newMeetingName.value = ''
      meetingDate.value = new Date().toISOString().split('T')[0]
      meetingTime.value = new Date().toTimeString().slice(0, 5)
      
      // Navigate to record page with the new meeting
      router.push(`/groups/${props.groupId}/record?meetingId=${result.id}`)
    }
  } catch (err: any) {
    createError.value = err.message || 'Failed to create meeting'
  } finally {
    isCreating.value = false
  }
}

// Reset form when dialog closes
const handleDialogChange = (open: boolean) => {
  isDialogOpen.value = open
  if (!open) {
    newMeetingName.value = ''
    createError.value = ''
    meetingDate.value = new Date().toISOString().split('T')[0]
    meetingTime.value = new Date().toTimeString().slice(0, 5)
  }
}
</script>

<template>
  <div class="space-y-8">
    <div class="space-y-4">
      <div class="flex justify-between items-center">
        <h2 class="text-xl font-semibold">Group Information</h2>
        
        <!-- Meeting Dialog -->
        <Dialog :open="isDialogOpen" @update:open="handleDialogChange">
          <DialogTrigger asChild>
            <Button @click="isDialogOpen = true">Start New Meeting</Button>
          </DialogTrigger>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>Create New Meeting</DialogTitle>
              <DialogDescription>
                Enter the details for your new meeting.
              </DialogDescription>
            </DialogHeader>
            
            <div class="py-4 space-y-4">
              <div class="space-y-2">
                <Label for="meeting-name">Meeting Name</Label>
                <Input 
                  id="meeting-name"
                  v-model="newMeetingName"
                  placeholder="Enter meeting name"
                />
              </div>
              
              <div class="grid grid-cols-2 gap-4">
                <div class="space-y-2">
                  <Label for="meeting-date">Date</Label>
                  <Input 
                    id="meeting-date"
                    v-model="meetingDate"
                    type="date"
                  />
                </div>
                <div class="space-y-2">
                  <Label for="meeting-time">Time</Label>
                  <Input 
                    id="meeting-time"
                    v-model="meetingTime"
                    type="time"
                  />
                </div>
              </div>
              
              <p v-if="createError" class="text-sm text-destructive">{{ createError }}</p>
            </div>
            
            <DialogFooter>
              <Button
                variant="outline" 
                @click="isDialogOpen = false"
              >
                Cancel
              </Button>
              <Button 
                @click="handleCreateMeeting"
                :disabled="isCreating || !newMeetingName.trim()"
              >
                <Loader2 v-if="isCreating" class="mr-2 h-4 w-4 animate-spin" />
                <span>{{ isCreating ? 'Creating...' : 'Create Meeting' }}</span>
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      </div>
      <div class="space-y-2">
        <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div class="p-4 border rounded-lg">
            <h3 class="font-medium">Group ID</h3>
            <p class="text-muted-foreground font-mono text-sm mt-1">{{ props.groupId }}</p>
          </div>
          <div class="p-4 border rounded-lg">
            <h3 class="font-medium">Created By</h3>
            <p class="text-muted-foreground mt-1">{{ props.currentGroup.created_by }}</p>
          </div>
        </div>
      </div>
    </div>

    <!-- Meetings List Section -->
    <div class="space-y-4">
      <div class="flex justify-between items-center">
        <h2 class="text-xl font-semibold">Meeting History</h2>
      </div>
      
      <!-- Loading state -->
      <div v-if="loading" class="py-8 text-center">
        <div class="inline-block h-6 w-6 animate-spin rounded-full border-2 border-solid border-current border-r-transparent"></div>
        <p class="mt-2 text-sm text-muted-foreground">Loading meetings...</p>
      </div>
      
      <!-- Error state -->
      <div v-else-if="error" class="py-8 text-center border rounded-lg">
        <p class="text-destructive">{{ error }}</p>
      </div>
      
      <!-- Meetings Table with shadcn-vue components -->
      <div v-else class="border rounded-lg">
        <Table>
          <TableCaption v-if="meetings.length === 0">No meetings available.</TableCaption>
          <TableHeader>
            <TableRow>
              <TableHead>Name</TableHead>
              <TableHead>Date & Time</TableHead>
              <TableHead class="text-right">Actions</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            <!-- No meetings state -->
            <TableEmpty v-if="meetings.length === 0" :colspan="3">
              <div class="flex flex-col items-center justify-center py-6">
                <div class="w-16 h-16 flex items-center justify-center rounded-full bg-muted mb-4">
                  <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="text-muted-foreground"><path d="M9.5 4h5L17 7h3a2 2 0 0 1 2 2v9a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V9a2 2 0 0 1 2-2h3l2.5-3z"></path><circle cx="12" cy="13" r="3"></circle></svg>
                </div>
                <h3 class="text-lg font-medium">No meetings yet</h3>
                <p class="text-muted-foreground mt-1 mb-4">Start recording a new meeting to get started</p>
                <Button @click="isDialogOpen = true" variant="outline" size="sm">Start New Meeting</Button>
              </div>
            </TableEmpty>
            
            <!-- Meetings list -->
            <TableRow 
              v-for="meeting in meetings" 
              :key="meeting.id" 
              class="cursor-pointer hover:bg-muted/50"
              @click="navigateToMeeting(meeting.id)"
            >
              <TableCell class="font-medium">{{ meeting.name }}</TableCell>
              <TableCell>{{ formatDateTime(meeting.meeting_datetime) }}</TableCell>
              <TableCell class="text-right">
                <Button variant="ghost" size="sm" @click.stop="navigateToMeeting(meeting.id)">
                  View
                </Button>
              </TableCell>
            </TableRow>
          </TableBody>
        </Table>
      </div>
    </div>
  </div>
</template>
