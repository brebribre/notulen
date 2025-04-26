<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useMeetings } from '@/hooks/useMeetings'
import { useAudioFiles } from '@/hooks/useAudioFiles'
import { formatDate } from '@/lib/utils'
import { Button } from '@/components/ui/button'
import { Separator } from '@/components/ui/separator'
import { Loader2, FileAudio, Calendar, Clock, Download, Pencil, Trash } from 'lucide-vue-next'
import {
  Card,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from '@/components/ui/card'

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
  fetchAudioByMeetingId
} = useMeetings()

const { 
  loading: audioLoading, 
  error: audioError,
  getAudioFileUrl
} = useAudioFiles()

// State
const audioFiles = ref<any[]>([])
const loadingAudioUrl = ref<Record<string, boolean>>({})

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

const formatFileSize = (bytes: number | null | undefined) => {
  if (bytes === null || bytes === undefined) return 'Unknown size'
  if (bytes < 1024) return bytes + ' bytes'
  else if (bytes < 1048576) return (bytes / 1024).toFixed(1) + ' KB'
  else return (bytes / 1048576).toFixed(1) + ' MB'
}

// Load data on mount
onMounted(loadMeetingData)
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
            <Button @click="navigateToRecord" variant="default">
              <FileAudio class="mr-2 h-4 w-4" />
              Record
            </Button>
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
        <div v-else class="grid gap-4 md:grid-cols-2">
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
              <div class="flex items-center justify-between">
                <div class="text-sm text-muted-foreground">
                  {{ formatFileSize(file.size) }}
                </div>
                <Button 
                  variant="outline" 
                  size="sm" 
                  @click="getAudioDownloadUrl(file.id)"
                  :disabled="loadingAudioUrl[file.id]"
                >
                  <Loader2 v-if="loadingAudioUrl[file.id]" class="mr-2 h-3 w-3 animate-spin" />
                  <Download v-else class="mr-2 h-3 w-3" />
                  Download
                </Button>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
      
      <!-- Transcript section -->
      <div v-if="currentMeeting.transcript" class="space-y-4">
        <h2 class="text-xl font-semibold">Transcript</h2>
        <div class="p-4 border rounded-lg bg-muted/20">
          <p class="whitespace-pre-line">{{ currentMeeting.transcript }}</p>
        </div>
      </div>
      
      <!-- Summary section -->
      <div v-if="currentMeeting.summary" class="space-y-4">
        <h2 class="text-xl font-semibold">Summary</h2>
        <div class="p-4 border rounded-lg bg-muted/20">
          <pre class="whitespace-pre-wrap">{{ JSON.stringify(currentMeeting.summary, null, 2) }}</pre>
        </div>
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
