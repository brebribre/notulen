<script setup lang="ts">
import { ref, onMounted, defineProps, defineEmits } from 'vue'
import { Button } from '@/components/ui/button'
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
import { Loader2, Upload, FileAudio, Calendar, Trash, RefreshCw } from 'lucide-vue-next'
import { useAudioFiles } from '@/hooks/useAudioFiles'

const props = defineProps<{
  groupId: string
}>()

const emit = defineEmits(['error'])

// Use the audio files hook
const { 
  audioFiles, 
  loading, 
  error,
  fetchAudioFiles,
  deleteAudioFile,
  uploadAudioFile,
  getAudioFileUrl,
  formatFileSize
} = useAudioFiles()

// Upload dialog
const showUploadDialog = ref(false)
const selectedFile = ref<File | null>(null)
const meetingDate = ref<string | undefined>(undefined)
const uploadLoading = ref(false)

// Load audio files
onMounted(async () => {
  try {
    await fetchAudioFiles(props.groupId)
  } catch (err) {
    if (err instanceof Error) {
      emit('error', err.message)
    }
  }
})

// Handle file selection
const handleFileChange = (event: Event) => {
  const input = event.target as HTMLInputElement
  if (input.files && input.files.length > 0) {
    selectedFile.value = input.files[0]
  }
}

// Upload file
const handleUpload = async () => {
  if (!selectedFile.value) return
  
  uploadLoading.value = true
  
  try {
    await uploadAudioFile(selectedFile.value, props.groupId, meetingDate.value)
    
    // Reset form
    resetUploadForm()
  } catch (err) {
    if (err instanceof Error) {
      emit('error', err.message)
    }
  } finally {
    uploadLoading.value = false
  }
}

// Reset upload form
const resetUploadForm = () => {
  selectedFile.value = null
  meetingDate.value = undefined
  showUploadDialog.value = false
}

// Handle file deletion
const handleDeleteFile = async (fileId: string) => {
  if (!confirm('Are you sure you want to delete this audio file?')) {
    return
  }
  
  try {
    await deleteAudioFile(fileId)
  } catch (err) {
    if (err instanceof Error) {
      emit('error', err.message)
    }
  }
}

// Handle getting download URL
const handleGetDownloadUrl = async (fileId: string) => {
  try {
    const url = await getAudioFileUrl(fileId)
    if (url) {
      window.open(url, '_blank')
    }
  } catch (err) {
    if (err instanceof Error) {
      emit('error', err.message)
    }
  }
}
</script>

<template>
  <div class="space-y-4">
    <div class="flex justify-between items-center">
      <h2 class="text-xl font-semibold">Audio Files</h2>
      
      <!-- Upload Dialog -->
      <Dialog v-model:open="showUploadDialog">
        <DialogTrigger asChild>
          <Button size="sm">
            <Upload class="mr-1 h-4 w-4" />
            Upload Audio
          </Button>
        </DialogTrigger>
        
        <DialogContent class="sm:max-w-[425px]">
          <DialogHeader>
            <DialogTitle>Upload Audio File</DialogTitle>
            <DialogDescription>
              Upload an audio recording for this group. Supported formats: MP3, WAV, M4A.
            </DialogDescription>
          </DialogHeader>
          
          <div class="space-y-4 py-4">
            <div class="space-y-2">
              <label class="text-sm font-medium leading-none" for="audioFile">Select Audio File</label>
              <Input 
                id="audioFile"
                type="file" 
                accept="audio/*"
                @change="handleFileChange"
              />
            </div>
            
            <div class="space-y-2">
              <label class="text-sm font-medium leading-none" for="meetingDate">Meeting Date (Optional)</label>
              <Input 
                id="meetingDate"
                v-model="meetingDate" 
                type="datetime-local"
              />
            </div>
            
            <!-- Selected File Info -->
            <div v-if="selectedFile" class="p-3 bg-primary/10 rounded-md">
              <div class="text-sm">
                <div class="font-medium">{{ selectedFile.name }}</div>
                <div class="text-muted-foreground">
                  {{ formatFileSize(selectedFile.size) }} • {{ selectedFile.type }}
                </div>
              </div>
            </div>
            
            <DialogFooter class="mt-6">
              <Button 
                variant="outline" 
                type="button"
                @click="resetUploadForm"
              >
                Cancel
              </Button>
              <Button 
                type="button" 
                @click="handleUpload"
                :disabled="uploadLoading || !selectedFile"
              >
                <Loader2 v-if="uploadLoading" class="mr-1 h-4 w-4 animate-spin" />
                {{ uploadLoading ? 'Uploading...' : 'Upload' }}
              </Button>
            </DialogFooter>
          </div>
        </DialogContent>
      </Dialog>
    </div>
    
    <!-- Loading State -->
    <div v-if="loading" class="flex justify-center py-8">
      <div class="flex flex-col items-center space-y-2">
        <Loader2 class="h-6 w-6 animate-spin text-primary" />
        <span class="text-sm text-muted-foreground">Loading audio files...</span>
      </div>
    </div>
    
    <!-- Error State -->
    <div v-else-if="error" class="p-4 bg-destructive/10 text-destructive rounded-lg">
      <p>{{ error }}</p>
      <Button 
        @click="fetchAudioFiles(props.groupId)" 
        variant="outline"
        size="sm"
        class="mt-2"
      >
        <RefreshCw class="mr-1 h-4 w-4" />
        Retry
      </Button>
    </div>
    
    <!-- Audio Files List -->
    <div v-else-if="audioFiles.length > 0" class="space-y-2">
      <div 
        v-for="file in audioFiles" 
        :key="file.id"
        class="flex items-center justify-between p-3 border rounded-lg hover:bg-accent/50 transition-colors"
      >
        <div class="flex items-center space-x-3">
          <div class="bg-muted rounded-full p-2">
            <FileAudio class="h-5 w-5 text-muted-foreground" />
          </div>
          <div>
            <div class="font-medium">{{ file.original_filename || 'Unnamed File' }}</div>
            <div class="text-sm text-muted-foreground">{{ formatFileSize(file.size) }}</div>
            <div v-if="file.meeting_datetime" class="flex items-center text-xs text-muted-foreground mt-1">
              <Calendar class="h-3 w-3 mr-1" />
              {{ new Date(file.meeting_datetime).toLocaleString() }}
            </div>
          </div>
        </div>
        
        <!-- Actions -->
        <div class="flex items-center space-x-2">
          <Button 
            variant="ghost" 
            size="sm"
            @click="handleGetDownloadUrl(file.id)"
          >
            Download
          </Button>
          
          <Button 
            variant="ghost" 
            size="sm"
            @click="handleDeleteFile(file.id)"
          >
            <Trash class="h-4 w-4 text-destructive" />
          </Button>
        </div>
      </div>
    </div>
    
    <!-- Empty State -->
    <div v-else class="text-center p-8 text-muted-foreground">
      <div class="mb-2 flex justify-center">
        <FileAudio class="h-10 w-10 text-muted-foreground/50" />
      </div>
      <h3 class="text-lg font-medium mb-1">No audio files</h3>
      <p class="text-sm">This group doesn't have any audio files yet.</p>
      <Button 
        variant="outline"
        size="sm"
        class="mt-4"
        @click="showUploadDialog = true"
      >
        <Upload class="mr-1 h-4 w-4" />
        Upload your first audio file
      </Button>
    </div>
  </div>
</template>
