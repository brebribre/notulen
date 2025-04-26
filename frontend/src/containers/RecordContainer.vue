<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { useAudioFiles } from '@/hooks/useAudioFiles'
import { Tooltip, TooltipTrigger, TooltipContent } from '@/components/ui/tooltip'
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter
} from '@/components/ui/dialog'

const route = useRoute()
const router = useRouter()
const { uploadAudioFile, loading } = useAudioFiles()

const groupId = route.params.groupId as string
const mediaRecorder = ref<MediaRecorder | null>(null)
const recordingStatus = ref<'inactive' | 'recording' | 'paused'>('inactive')
const audioChunks = ref<BlobPart[]>([])
const audioUrl = ref<string | null>(null)
const recordingDuration = ref(0)
const recordingTimer = ref<number | null>(null)
const errorMessage = ref<string | null>(null)

// Dialog and meeting data
const showSaveDialog = ref(false)
const meetingName = ref('')
const meetingDate = ref(new Date().toISOString())

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

// Start recording
const startRecording = () => {
  if (!mediaRecorder.value) return
  
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

// Open save dialog
const openSaveDialog = () => {
  // Set default name based on date
  const now = new Date()
  meetingName.value = `Meeting ${now.toLocaleDateString()}`
  meetingDate.value = now.toISOString()
  showSaveDialog.value = true
}

// Save recording to Supabase
const saveRecording = async () => {
  if (!audioUrl.value) return
  
  try {
    const response = await fetch(audioUrl.value)
    const blob = await response.blob()
    
    // Create filename with meeting name
    const sanitizedName = meetingName.value.replace(/[^a-z0-9]/gi, '_').toLowerCase()
    const filename = `${sanitizedName}-${Date.now()}.wav`
    const file = new File([blob], filename, { type: 'audio/wav' })
    
    // Upload to Supabase using the hook
    await uploadAudioFile(file, groupId, meetingDate.value)
    
    // Navigate back to details page
    router.push(`/groups/${groupId}`)
  } catch (err) {
    console.error('Error saving recording:', err)
    errorMessage.value = 'Failed to save recording. Please try again.'
    showSaveDialog.value = false
  }
}

// Go back to previous page
const goBack = () => {
  router.push(`/groups/${groupId}`)
}

// Set up recorder on mount
onMounted(() => {
  setupRecorder()
})

// Clean up on unmount
onUnmounted(() => {
  stopTimer()
  if (audioUrl.value) {
    URL.revokeObjectURL(audioUrl.value)
  }
})
</script>

<template>
  <div class="p-4 space-y-6">
    <!-- Header -->
    <div class="flex justify-between items-center">
      <h1 class="text-2xl font-bold">Record Meeting</h1>
      <Button variant="outline" @click="goBack">Cancel</Button>
    </div>
    
    <!-- Error message -->
    <div v-if="errorMessage" class="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded relative">
      {{ errorMessage }}
    </div>
    
    <!-- Recording interface -->
    <div class="flex flex-col items-center space-y-6 py-4">
      <!-- Recording visualization/status -->
      <div class="w-full max-w-md h-24 bg-gray-100 rounded-lg flex items-center justify-center">
        <div v-if="recordingStatus === 'recording'" class="text-red-500 flex items-center gap-2">
          <span class="animate-pulse h-3 w-3 bg-red-500 rounded-full"></span>
          Recording {{ formatTime(recordingDuration) }}
        </div>
        <div v-else-if="audioUrl" class="w-full px-4">
          <audio :src="audioUrl" controls class="w-full"></audio>
        </div>
        <div v-else class="text-gray-500">
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
              :disabled="!mediaRecorder">
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
            <p>{{ recordingStatus === 'inactive' ? 'Start Recording' : 'Stop Recording' }}</p>
          </TooltipContent>
        </Tooltip>
      </div>
      
      <!-- Save button -->
      <Button 
        v-if="audioUrl" 
        @click="openSaveDialog" 
        :disabled="loading" 
        variant="default" 
        class="mt-6">
        Save Recording
      </Button>
    </div>
    
    <!-- Save dialog -->
    <Dialog :open="showSaveDialog" @update:open="showSaveDialog = $event">
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Save Meeting Recording</DialogTitle>
          <DialogDescription>
            Enter a name for this meeting recording.
          </DialogDescription>
        </DialogHeader>
        
        <div class="grid gap-4 py-4">
          <div class="grid grid-cols-4 items-center gap-4">
            <label for="name" class="text-right">Meeting name</label>
            <Input
              id="name"
              v-model="meetingName"
              placeholder="Enter meeting name"
              class="col-span-3"
            />
          </div>
          <div class="grid grid-cols-4 items-center gap-4">
            <label class="text-right">Date</label>
            <div class="col-span-3 text-sm text-muted-foreground">
              {{ new Date(meetingDate).toLocaleString() }}
            </div>
          </div>
        </div>
        
        <DialogFooter>
          <Button variant="outline" @click="showSaveDialog = false">Cancel</Button>
          <Button 
            @click="saveRecording" 
            :disabled="loading || !meetingName.trim()">
            {{ loading ? 'Saving...' : 'Save' }}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  </div>
</template>
