<script setup lang="ts">
import { ref, onMounted, onUnmounted, computed, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useMeetings } from '@/hooks/useMeetings'
import { useAudioFiles } from '@/hooks/useAudioFiles'
import { formatDate } from '@/lib/utils'
import { Button } from '@/components/ui/button'
import { Separator } from '@/components/ui/separator'
import { Loader2, FileAudio, Calendar, Clock, Download, Trash2, AlertCircle, CheckCircle2, User, Tag } from 'lucide-vue-next'
import {
  Card,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from '@/components/ui/card'
import { Tooltip, TooltipTrigger, TooltipContent } from '@/components/ui/tooltip'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '@/components/ui/dialog'
import {
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
} from '@/components/ui/accordion'

// Route params
const route = useRoute()
const router = useRouter()
const meetingId = computed(() => route.params.meetingId as string)
const groupId = computed(() => route.params.groupId as string)

// Hooks
const { 
  currentMeeting, 
  loading: meetingLoading, 
  error: meetingError, 
  fetchMeeting,
  fetchAudioByMeetingId,
  updateMeeting,
  clearMeetingTranscriptAndSummary
} = useMeetings()

const { 
  loading: audioLoading, 
  error: audioError,
  getAudioFileUrl,
  deleteAudioFile
} = useAudioFiles()

// State
const audioFiles = ref<any[]>([])
const loadingAudioUrl = ref<Record<string, boolean>>({})
const deletingAudio = ref<Record<string, boolean>>({})
const showDeleteDialog = ref(false)
const audioToDelete = ref<any>(null)
const deleteError = ref<string | null>(null)
const pollingInterval = ref<number | null>(null)
const pollCount = ref(0)
const MAX_POLL_COUNT = 60 // Stop polling after 10 minutes (60 * 10 seconds)

// Computed properties
const loading = computed(() => meetingLoading.value || audioLoading.value)
const error = computed(() => meetingError.value || audioError.value)
const formattedDate = computed(() => {
  if (!currentMeeting.value?.meeting_datetime) return ''
  return formatDate(new Date(currentMeeting.value.meeting_datetime), 'PPP') // Long date format
})
const formattedTime = computed(() => {
  if (!currentMeeting.value?.meeting_datetime) return ''
  return formatDate(new Date(currentMeeting.value.meeting_datetime), 'p') // Time format
})

// Check if we're waiting for transcript/summary to be processed
const isWaitingForProcessing = computed(() => {
  // If we have audio files but no transcript/summary, it's likely still processing
  return audioFiles.value.length > 0 && 
    (!hasTranscriptContent.value || !hasSummaryContent.value)
})

// Check if summary has content
const hasSummaryContent = computed(() => {
  if (!currentMeeting.value?.summary) return false
  
  // Check if summary is an empty object
  if (Object.keys(currentMeeting.value.summary).length === 0) return false
  
  // Check if summary has essential content (summary text)
  return !!currentMeeting.value.summary.summary
})

// Check if transcript has content
const hasTranscriptContent = computed(() => {
  return !!currentMeeting.value?.transcript && currentMeeting.value.transcript.trim() !== ''
})

// Methods
const loadMeetingData = async () => {
  if (!meetingId.value) return
  
  try {
    await fetchMeeting(meetingId.value)
    
    // Once meeting is loaded, fetch associated audio files
    const audioData = await fetchAudioByMeetingId(meetingId.value)
    audioFiles.value = audioData
  } catch (err) {
    console.error('Error loading meeting data:', err)
  }
}

// Poll for updates when processing
const startPolling = () => {
  // Clear any existing interval
  stopPolling()
  
  // Reset poll count
  pollCount.value = 0
  
  // Start new interval
  pollingInterval.value = window.setInterval(async () => {
    // Increment poll count
    pollCount.value++
    
    // Check if we should stop polling
    if (pollCount.value >= MAX_POLL_COUNT) {
      stopPolling()
      return
    }
    
    try {
      // Fetch fresh meeting data without triggering loading state
      const freshMeeting = await fetchMeeting(meetingId.value, false)
      
      if (freshMeeting) {
        // Update the current meeting reactively
        currentMeeting.value = freshMeeting
        
        // Also fetch associated audio files without triggering loading state
        const audioData = await fetchAudioByMeetingId(meetingId.value, false)
        if (audioData) {
          audioFiles.value = audioData
        }
        
        // If we now have transcript and summary, stop polling
        if (
          (freshMeeting.transcript && freshMeeting.transcript.trim() !== '') &&
          (freshMeeting.summary && Object.keys(freshMeeting.summary).length > 0 && freshMeeting.summary.summary)
        ) {
          stopPolling()
        }
      }
    } catch (err) {
      console.error('Error polling for updates:', err)
    }
  }, 10000) // Poll every 10 seconds
}

// Stop polling
const stopPolling = () => {
  if (pollingInterval.value !== null) {
    clearInterval(pollingInterval.value)
    pollingInterval.value = null
  }
}

// Watch for changes in processing status
watch(isWaitingForProcessing, (newValue) => {
  if (newValue) {
    // Start polling if we're waiting for processing
    startPolling()
  } else {
    // Stop polling if we're no longer waiting
    stopPolling()
  }
})

const navigateToRecord = () => {
  router.push(`/groups/${groupId.value}/record?meetingId=${meetingId.value}`)
}

const getAudioDownloadUrl = async (fileId: string) => {
  loadingAudioUrl.value[fileId] = true
  try {
    const url = await getAudioFileUrl(fileId)
    if (url) {
      window.open(url, '_blank')
    }
  } catch (err) {
    console.error('Error getting audio download URL:', err)
  } finally {
    loadingAudioUrl.value[fileId] = false
  }
}

const openDeleteDialog = (file: any) => {
  audioToDelete.value = file
  showDeleteDialog.value = true
  deleteError.value = null
}

const confirmDeleteAudio = async () => {
  if (!audioToDelete.value) return
  
  const fileId = audioToDelete.value.id
  deletingAudio.value[fileId] = true
  deleteError.value = null
  
  try {
    // Delete the audio file
    await deleteAudioFile(fileId)
    
    // Remove the file from the list
    audioFiles.value = audioFiles.value.filter(file => file.id !== fileId)
    
    // Clear transcript and summary in the meeting
    if (currentMeeting.value) {
      await clearMeetingTranscriptAndSummary(meetingId.value)
    }
    
    showDeleteDialog.value = false
    audioToDelete.value = null
    
    // Refresh meeting data to ensure transcript/summary are updated
    await fetchMeeting(meetingId.value)
  } catch (err) {
    console.error('Error deleting audio file:', err)
    deleteError.value = 'Failed to delete the audio file. Please try again.'
  } finally {
    deletingAudio.value[fileId] = false
  }
}

const cancelDelete = () => {
  showDeleteDialog.value = false
  audioToDelete.value = null
  deleteError.value = null
}

const formatFileSize = (bytes: number | null | undefined) => {
  if (bytes === null || bytes === undefined) return 'Unknown size'
  if (bytes < 1024) return bytes + ' bytes'
  else if (bytes < 1048576) return (bytes / 1024).toFixed(1) + ' KB'
  else return (bytes / 1048576).toFixed(1) + ' MB'
}

// Load data on mount
onMounted(async () => {
  await loadMeetingData()
  
  // Check if we need to start polling
  if (isWaitingForProcessing.value) {
    startPolling()
  }
})

// Clean up on unmount
onUnmounted(() => {
  stopPolling()
})
</script>

<template>
  <div class="container p-4 mx-auto">
    <!-- Loading state -->
    <div v-if="loading" class="flex flex-col items-center justify-center my-12 space-y-4">
      <Loader2 class="h-8 w-8 mx-auto animate-spin text-primary" />
      <p class="mt-2 text-muted-foreground">Loading meeting details...</p>
    </div>
    
    <!-- Error state -->
    <div v-else-if="error" class="p-4 bg-destructive/10 text-destructive rounded-lg mb-4">
      <p>{{ error }}</p>
      <Button @click="loadMeetingData" variant="outline" size="sm" class="mt-2">Try Again</Button>
    </div>
    
    <!-- Meeting details -->
    <div v-else-if="currentMeeting" class="space-y-8">
      <div class="relative space-y-4">
        <div class="flex justify-between items-start">
          <div>
            <h1 class="text-3xl font-bold">{{ currentMeeting.name }}</h1>
            <div class="flex items-center mt-2 space-x-6 text-muted-foreground">
              <div class="flex items-center">
                <Calendar class="mr-1 h-4 w-4" />
                <span>{{ formattedDate }}</span>
              </div>
              <div class="flex items-center">
                <Clock class="mr-1 h-4 w-4" />
                <span>{{ formattedTime }}</span>
              </div>
            </div>
          </div>
          
          <div class="flex space-x-2">
            <Tooltip>
              <TooltipTrigger>
                <Button 
                  @click="navigateToRecord" 
                  variant="default"
                  :disabled="audioFiles.length > 0">
                  <FileAudio class="mr-2 h-4 w-4" />
                  Record
                </Button>
              </TooltipTrigger>
              <TooltipContent v-if="audioFiles.length > 0">
                <p>This meeting already has an audio recording</p>
              </TooltipContent>
              <TooltipContent v-else>
                <p>Record audio for this meeting</p>
              </TooltipContent>
            </Tooltip>
          </div>
        </div>
        
        <div class="text-sm text-muted-foreground">
          Created: {{ formatDate(new Date(currentMeeting.created_at), 'PPP') }}
        </div>
        
        <Separator />
      </div>
      
      <!-- Audio recordings section -->
      <div class="space-y-6">
        <h2 class="text-xl font-semibold">Audio Recordings</h2>
        
        <div v-if="audioFiles.length === 0" class="bg-muted/40 rounded-lg py-12 px-6 text-center">
          <FileAudio class="h-12 w-12 mx-auto text-muted-foreground mb-4" />
          <h3 class="text-lg font-medium">No recordings yet</h3>
          <p class="text-muted-foreground mt-1 mb-4">This meeting doesn't have any audio recordings yet.</p>
          <Button @click="navigateToRecord" variant="outline">Record Meeting</Button>
        </div>
        
        <!-- Audio files list -->
        <div v-else class="grid gap-4">
          <Card v-for="file in audioFiles" :key="file.id" class="overflow-hidden">
            <CardHeader>
              <CardTitle class="text-base truncate">
                {{ file.original_filename || 'Untitled Recording' }}
              </CardTitle>
              <CardDescription>
                Recorded: {{ formatDate(new Date(file.created_at), 'PPp') }}
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div class="text-sm text-muted-foreground">
                {{ formatFileSize(file.size) }}
              </div>
            </CardContent>
            <CardFooter className="pt-0 flex justify-between mb-6 mx-6">
              <Button 
                variant="outline" 
                size="sm" 
                @click="getAudioDownloadUrl(file.id)"
                :disabled="loadingAudioUrl[file.id] || deletingAudio[file.id]"
              >
                <Loader2 v-if="loadingAudioUrl[file.id]" class="mr-2 h-3 w-3 animate-spin" />
                <Download v-else class="mr-2 h-3 w-3" />
                Download
              </Button>
              
              <Button 
                variant="destructive" 
                size="sm" 
                @click="openDeleteDialog(file)"
                :disabled="deletingAudio[file.id] || loadingAudioUrl[file.id]"
              >
                <Loader2 v-if="deletingAudio[file.id]" class="mr-2 h-3 w-3 animate-spin" />
                <Trash2 v-else class="mr-2 h-3 w-3" />
                Delete
              </Button>
            </CardFooter>
          </Card>
        </div>
        
        <!-- Delete confirmation dialog -->
        <Dialog v-model:open="showDeleteDialog">
          <DialogContent>
            <DialogHeader>
              <DialogTitle>Delete Audio Recording</DialogTitle>
              <DialogDescription>
                Are you sure you want to delete this audio recording?
                <div class="mt-2 font-medium">{{ audioToDelete?.original_filename }}</div>
              </DialogDescription>
            </DialogHeader>
            
            <div v-if="deleteError" class="mt-2 p-3 bg-destructive/10 text-destructive rounded flex items-start">
              <AlertCircle class="h-5 w-5 mr-2 flex-shrink-0 mt-0.5" />
              <span>{{ deleteError }}</span>
            </div>
            
            <DialogFooter class="mt-4">
              <Button variant="outline" @click="cancelDelete">Cancel</Button>
              <Button 
                variant="destructive" 
                @click="confirmDeleteAudio"
                :disabled="deletingAudio[audioToDelete?.id]"
              >
                <Loader2 v-if="deletingAudio[audioToDelete?.id]" class="mr-2 h-4 w-4 inline animate-spin" />
                Delete
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      </div>
      
      <!-- Processing indicator -->
      <div v-if="isWaitingForProcessing" class="p-4 bg-amber-50 border border-amber-200 text-amber-800 rounded-lg">
        <div class="flex items-center space-x-3">
          <Loader2 class="h-5 w-5 animate-spin text-amber-600" />
          <div>
            <h3 class="font-medium">Processing audio</h3>
            <p class="text-sm">We're generating the transcript and summary from your audio file. This may take a few minutes.</p>
          </div>
        </div>
      </div>
      
      <!-- Summary section -->
      <div v-if="hasSummaryContent" class="space-y-4">
        <h2 class="text-xl font-semibold">Summary</h2>
        <Card>
          <CardHeader>
            <CardTitle>Meeting Summary</CardTitle>
            <CardDescription>AI-generated summary of the meeting content</CardDescription>
          </CardHeader>
          <CardContent class="space-y-6">
            <!-- Main summary text -->
            <div v-if="currentMeeting?.summary?.summary" class="space-y-2">
              <p class="text-muted-foreground text-sm font-medium">Overview</p>
              <p class="text-foreground">{{ currentMeeting.summary.summary }}</p>
            </div>
            
            <!-- Action items list -->
            <div v-if="currentMeeting?.summary?.action_items && currentMeeting.summary.action_items.length > 0" class="space-y-2">
              <p class="text-muted-foreground text-sm font-medium">Action Items</p>
              <ul class="space-y-1">
                <li v-for="(item, index) in currentMeeting.summary.action_items" :key="index" class="flex items-start">
                  <CheckCircle2 class="h-5 w-5 mr-2 text-green-500 flex-shrink-0 mt-0.5" />
                  <span>{{ item }}</span>
                </li>
              </ul>
            </div>
            
            <!-- Participants list -->
            <div v-if="currentMeeting?.summary?.participants && currentMeeting.summary.participants.length > 0" class="space-y-2">
              <p class="text-muted-foreground text-sm font-medium">Participants</p>
              <div class="flex flex-wrap gap-2">
                <div 
                  v-for="(participant, index) in currentMeeting.summary.participants" 
                  :key="index"
                  class="flex items-center px-3 py-1 bg-muted rounded-full text-sm"
                >
                  <User class="h-3.5 w-3.5 mr-1.5 text-muted-foreground" />
                  <span>{{ participant }}</span>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
      
      <!-- Summary processing indicator -->
      <div v-else-if="audioFiles.length > 0 && !hasSummaryContent" class="space-y-4">
        <h2 class="text-xl font-semibold">Summary</h2>
        <Card>
          <CardContent class="py-6">
            <div class="flex flex-col items-center justify-center text-center p-4">
              <Loader2 class="h-8 w-8 animate-spin text-muted-foreground mb-4" />
              <h3 class="text-lg font-medium">Generating summary</h3>
              <p class="text-muted-foreground mt-1">We're processing your audio to generate a meeting summary.</p>
            </div>
          </CardContent>
        </Card>
      </div>
      
      <!-- Transcript section -->
      <div v-if="hasTranscriptContent" class="space-y-4">
        <h2 class="text-xl font-semibold">Transcript</h2>
        <Card>
          <CardHeader>
            <CardTitle>Meeting Transcript</CardTitle>
            <CardDescription>AI-generated transcription of the audio recording</CardDescription>
          </CardHeader>
          <CardContent>
            <Accordion type="single" collapsible class="w-full">
              <AccordionItem value="transcript">
                <AccordionTrigger>View Transcript</AccordionTrigger>
                <AccordionContent>
                  <div class="p-4 rounded-md bg-muted/20 max-h-96 overflow-y-auto mt-2">
                    <p class="whitespace-pre-line text-sm">{{ currentMeeting.transcript }}</p>
                  </div>
                </AccordionContent>
              </AccordionItem>
            </Accordion>
          </CardContent>
        </Card>
      </div>
      
      <!-- Transcript processing indicator -->
      <div v-else-if="audioFiles.length > 0 && !hasTranscriptContent" class="space-y-4">
        <h2 class="text-xl font-semibold">Transcript</h2>
        <Card>
          <CardContent class="py-6">
            <div class="flex flex-col items-center justify-center text-center p-4">
              <Loader2 class="h-8 w-8 animate-spin text-muted-foreground mb-4" />
              <h3 class="text-lg font-medium">Generating transcript</h3>
              <p class="text-muted-foreground mt-1">We're converting your audio to text. This may take a few minutes.</p>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
    
    <!-- Not found state -->
    <div v-else class="text-center p-8">
      <h1 class="text-2xl font-bold mb-2">Meeting Not Found</h1>
      <p class="text-muted-foreground mb-4">The meeting you are looking for does not exist or you do not have access to it.</p>
      <Button @click="router.push(`/groups/${groupId}`)" variant="outline">Back to Group</Button>
    </div>
  </div>
</template>
