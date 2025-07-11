<script setup lang="ts">
import { ref, onMounted, onUnmounted, computed } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { Button } from '@/components/ui/button'
import { useAudioFiles } from '@/hooks/useAudioFiles'
import { useMeetings } from '@/hooks/useMeetings'
import { Tooltip, TooltipTrigger, TooltipContent } from '@/components/ui/tooltip'
import { Loader2, UploadCloud, AlertCircle } from 'lucide-vue-next'
import { 
  Tabs, 
  TabsContent, 
  TabsList, 
  TabsTrigger 
} from '@/components/ui/tabs'

const route = useRoute()
const router = useRouter()
const { uploadAudioFile, loading: uploadLoading } = useAudioFiles()
const { fetchMeeting, fetchAudioByMeetingId, loading: meetingLoading } = useMeetings()

const groupId = route.params.groupId as string
const meetingId = computed(() => route.query.meetingId as string | undefined)
const loading = computed(() => uploadLoading.value || meetingLoading.value)

const mediaRecorder = ref<MediaRecorder | null>(null)
const recordingStatus = ref<'inactive' | 'recording' | 'paused'>('inactive')
const audioChunks = ref<BlobPart[]>([])
const audioUrl = ref<string | null>(null)
const recordingDuration = ref(0)
const recordingTimer = ref<number | null>(null)
const errorMessage = ref<string | null>(null)

// Dialog and meeting data
const meetingName = ref('')
const meetingDate = ref(new Date().toISOString())
const meeting = ref<any>(null)
const existingAudioFiles = ref<any[]>([])
const hasExistingAudio = computed(() => existingAudioFiles.value.length > 0)

// File upload state
const selectedFile = ref<File | null>(null)
const fileInputRef = ref<HTMLInputElement | null>(null)
const activeTab = ref('record')
const isSaving = ref(false)

// Request microphone access and set up recorder
const setupRecorder = async () => {
  try {
    const stream = await navigator.mediaDevices.getUserMedia({ audio: true })
    
    mediaRecorder.value = new MediaRecorder(stream)
    
    mediaRecorder.value.ondataavailable = (event) => {
      if (event.data.size > 0) {
        audioChunks.value.push(event.data)
      }
    }

    mediaRecorder.value.onstop = () => {
      const audioBlob = new Blob(audioChunks.value, { type: 'audio/wav' })
      audioUrl.value = URL.createObjectURL(audioBlob)
      stopTimer()
    }

    errorMessage.value = null
  } catch (err) {
    console.error('Error accessing microphone:', err)
    errorMessage.value = 'Could not access microphone. Please check permissions.'
  }
}

// Load meeting data if meetingId is provided
const loadMeetingData = async () => {
  if (meetingId.value) {
    try {
      // Fetch the meeting data
      const meetingData = await fetchMeeting(meetingId.value)
      if (meetingData) {
        meeting.value = meetingData
        meetingName.value = meetingData.name
        meetingDate.value = meetingData.meeting_datetime
      }
      
      // Fetch any audio files associated with this meeting
      const audioData = await fetchAudioByMeetingId(meetingId.value)
      existingAudioFiles.value = audioData || []
      
      // If there's already an audio file, show a warning
      if (hasExistingAudio.value) {
        errorMessage.value = 'This meeting already has an audio recording. You cannot add another one.'
      }
    } catch (err) {
      console.error('Error loading meeting data:', err)
      errorMessage.value = 'Failed to load meeting data.'
    }
  }
}

// Start recording
const startRecording = () => {
  if (!mediaRecorder.value || hasExistingAudio.value) return
  
  audioChunks.value = []
  audioUrl.value = null
  mediaRecorder.value.start()
  recordingStatus.value = 'recording'
  startTimer()
}

// Stop recording
const stopRecording = () => {
  if (!mediaRecorder.value || recordingStatus.value === 'inactive') return
  
  mediaRecorder.value.stop()
  recordingStatus.value = 'inactive'
  stopTimer()
}

// Start timer to track recording duration
const startTimer = () => {
  recordingDuration.value = 0
  recordingTimer.value = window.setInterval(() => {
    recordingDuration.value++
  }, 1000)
}

// Stop the timer
const stopTimer = () => {
  if (recordingTimer.value) {
    clearInterval(recordingTimer.value)
    recordingTimer.value = null
  }
}

// Format seconds as mm:ss
const formatTime = (seconds: number) => {
  const mins = Math.floor(seconds / 60).toString().padStart(2, '0')
  const secs = (seconds % 60).toString().padStart(2, '0')
  return `${mins}:${secs}`
}

// Handle file selection
const handleFileChange = (event: Event) => {
  if (hasExistingAudio.value) return
  
  const input = event.target as HTMLInputElement
  if (input.files && input.files.length > 0) {
    selectedFile.value = input.files[0]
    // Reset any recording that might exist
    audioUrl.value = null
    recordingStatus.value = 'inactive'
  }
}

// Trigger file input click
const triggerFileInput = () => {
  if (fileInputRef.value && !hasExistingAudio.value) {
    fileInputRef.value.click()
  }
}


// Check if save is possible
const canSave = computed(() => {
  if (hasExistingAudio.value) return false
  return (activeTab.value === 'record' && audioUrl.value) || 
         (activeTab.value === 'upload' && selectedFile.value)
})

// Save audio directly without showing the dialog
const saveAudio = async () => {
  if (!canSave.value || !meetingId.value || hasExistingAudio.value) {
    errorMessage.value = hasExistingAudio.value 
      ? "Cannot save: This meeting already has an audio recording." 
      : "Cannot save: missing audio or meeting ID";
    return;
  }
  
  isSaving.value = true;
  
  try {
    let file: File;
    
    if (activeTab.value === 'record' && audioUrl.value) {
      // Handle recording
      const response = await fetch(audioUrl.value);
      const blob = await response.blob();
      
      // Create filename using meeting info if available
      const nameBase = meeting.value ? meeting.value.name.replace(/[^a-z0-9]/gi, '_').toLowerCase() : 'recording';
      const filename = `${nameBase}-${Date.now()}.wav`;
      file = new File([blob], filename, { type: 'audio/wav' });
    } else if (activeTab.value === 'upload' && selectedFile.value) {
      // Use the uploaded file directly
      file = selectedFile.value;
    } else {
      throw new Error('No file available to save');
    }
    
    // Get meeting date if available, otherwise use current date
    const audioDate = meeting.value ? meeting.value.meeting_datetime : new Date().toISOString();
    
    // Upload to Supabase using the hook
    await uploadAudioFile(file, groupId, audioDate, meetingId.value);
    
    // Navigate back to meeting details page
    router.push(`/groups/${groupId}/meetings/${meetingId.value}`);
  } catch (err) {
    console.error('Error saving audio:', err);
    errorMessage.value = 'Failed to save audio. Please try again.';
  } finally {
    isSaving.value = false;
  }
}

// Go back to previous page
const goBack = () => {
  router.push(`/groups/${groupId}`)
}

// Clean up function
const cleanUp = () => {
  // Reset file input
  if (fileInputRef.value) {
    fileInputRef.value.value = ''
  }
  selectedFile.value = null
  
  // Reset recording
  stopTimer()
  if (audioUrl.value) {
    URL.revokeObjectURL(audioUrl.value)
    audioUrl.value = null
  }
  audioChunks.value = []
  recordingStatus.value = 'inactive'
}

// Set up recorder on mount
onMounted(async () => {
  await setupRecorder()
  if (meetingId.value) {
    await loadMeetingData()
  }
})

// Clean up on unmount
onUnmounted(() => {
  cleanUp()
})
</script>

<template>
  <div class="container p-4 mx-auto">
    <!-- Header -->
    <div class="flex justify-between items-center mb-6">
      <h1 class="text-2xl font-bold">
        {{ meeting ? `Record Audio for: ${meeting.name}` : 'Record Meeting Audio' }}
      </h1>
      <Button variant="outline" @click="goBack">Cancel</Button>
    </div>
    
    <!-- Error message -->
    <div v-if="errorMessage" class="bg-destructive/10 border border-destructive/20 text-destructive px-4 py-3 rounded-lg mb-6 flex items-center">
      <AlertCircle class="h-5 w-5 mr-2 flex-shrink-0" />
      <span>{{ errorMessage }}</span>
    </div>
    
    <!-- Existing audio warning -->
    <div v-if="hasExistingAudio" class="bg-amber-50 border border-amber-200 text-amber-800 px-4 py-6 rounded-lg mb-6 text-center">
      <h3 class="text-lg font-semibold mb-2">This meeting already has an audio recording</h3>
      <p class="mb-4">You cannot add another audio recording to this meeting.</p>
      <Button variant="outline" @click="goBack">Go Back</Button>
    </div>
    
    <!-- Main content -->
    <div v-if="!hasExistingAudio">
      <!-- Tabs for recording vs uploading -->
      <Tabs v-model="activeTab" class="w-full max-w-2xl mx-auto" @update:modelValue="cleanUp">
        <TabsList class="grid w-full grid-cols-2 mb-6">
          <TabsTrigger value="record" class="flex items-center gap-2">
            Record New
          </TabsTrigger>
          <TabsTrigger value="upload" class="flex items-center gap-2">
            Upload File
          </TabsTrigger>
        </TabsList>
        
        <!-- Recording Tab -->
        <TabsContent value="record" class="py-4">
          <div class="flex flex-col items-center space-y-6">
            <!-- Recording visualization/status -->
            <div class="w-full max-w-md h-24 bg-muted rounded-lg flex items-center justify-center">
              <div v-if="recordingStatus === 'recording'" class="text-destructive flex items-center gap-2">
                <span class="animate-pulse h-3 w-3 bg-destructive rounded-full"></span>
                Recording {{ formatTime(recordingDuration) }}
              </div>
              <div v-else-if="audioUrl" class="w-full px-4">
                <audio :src="audioUrl" controls class="w-full"></audio>
              </div>
              <div v-else class="text-muted-foreground">
                Ready to record
              </div>
            </div>
            
            <!-- Recording controls -->
            <div class="flex gap-4">
              <Tooltip>
                <TooltipTrigger>
                  <Button 
                    v-if="recordingStatus === 'inactive'" 
                    @click="startRecording" 
                    class="h-16 w-16 rounded-full"
                    variant="default"
                    :disabled="!mediaRecorder || hasExistingAudio">
                    <svg xmlns="http://www.w3.org/2000/svg" class="h-8 w-8" viewBox="0 0 20 20" fill="currentColor">
                      <circle cx="10" cy="10" r="6" />
                    </svg>
                  </Button>
                  <Button 
                    v-else 
                    @click="stopRecording" 
                    class="h-16 w-16 rounded-full"
                    variant="destructive">
                    <svg xmlns="http://www.w3.org/2000/svg" class="h-8 w-8" viewBox="0 0 20 20" fill="currentColor">
                      <rect x="6" y="6" width="8" height="8" />
                    </svg>
                  </Button>
                </TooltipTrigger>
                <TooltipContent>
                  <p v-if="hasExistingAudio">Recording disabled: This meeting already has an audio file</p>
                  <p v-else>{{ recordingStatus === 'inactive' ? 'Start Recording' : 'Stop Recording' }}</p>
                </TooltipContent>
              </Tooltip>
            </div>
          </div>
        </TabsContent>
        
        <!-- Upload Tab -->
        <TabsContent value="upload" class="py-4">
          <div class="flex flex-col items-center space-y-6">
            <!-- File upload area -->
            <div 
              @click="triggerFileInput"
              class="w-full max-w-md h-40 bg-muted rounded-lg flex flex-col items-center justify-center p-6 border-2 border-dashed border-muted-foreground/20 cursor-pointer hover:bg-muted/80 transition-colors"
              :class="{ 'opacity-50 cursor-not-allowed': hasExistingAudio }"
            >
              <Tooltip>
                <TooltipTrigger class="w-full h-full flex flex-col items-center justify-center">
                  <input 
                    ref="fileInputRef"
                    type="file" 
                    accept="audio/*" 
                    class="hidden" 
                    @change="handleFileChange"
                    :disabled="hasExistingAudio"
                  />
                  
                  <UploadCloud class="h-12 w-12 text-muted-foreground mb-3" />
                  
                  <div v-if="selectedFile" class="text-center">
                    <p class="text-foreground font-medium">{{ selectedFile.name }}</p>
                    <p class="text-sm text-muted-foreground">
                      {{ (selectedFile.size / 1024 / 1024).toFixed(2) }} MB
                    </p>
                  </div>
                  <div v-else class="text-center">
                    <p class="text-foreground font-medium">Click to select an audio file</p>
                    <p class="text-sm text-muted-foreground">Or drag and drop a file here</p>
                    <p class="text-xs text-muted-foreground mt-2">Supports: MP3, WAV, M4A, etc.</p>
                  </div>
                </TooltipTrigger>
                <TooltipContent v-if="hasExistingAudio">
                  <p>Upload disabled: This meeting already has an audio file</p>
                </TooltipContent>
              </Tooltip>
            </div>
          </div>
        </TabsContent>
      </Tabs>
      
      <!-- Save button -->
      <div class="flex justify-center mt-8">
        <Tooltip>
          <TooltipTrigger class="w-full max-w-md">
            <Button 
              @click="saveAudio" 
              :disabled="loading || isSaving || !canSave || hasExistingAudio" 
              variant="default" 
              size="lg"
              class="w-full">
              <span v-if="isSaving">
                <Loader2 class="mr-2 h-4 w-4 inline animate-spin" />
                Saving...
              </span>
              <span v-else>Save Audio</span>
            </Button>
          </TooltipTrigger>
          <TooltipContent v-if="hasExistingAudio">
            <p>Save disabled: This meeting already has an audio file</p>
          </TooltipContent>
        </Tooltip>
      </div>
    </div>
  </div>
</template>
