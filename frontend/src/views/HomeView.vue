<script setup lang="ts">
// Inbox view component
import HomeNavbar from '@/components/HomeNavbar.vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const router = useRouter()
const authStore = useAuthStore()

const navigateToLogin = () => {
  router.push('/login')
}

const navigateToRegister = () => {
  router.push('/register')
}

const navigateToDashboard = () => {
  router.push('/app')
}
</script>

<template>
  <div class="min-h-screen flex flex-col">
    
    <main class="flex-1 flex flex-col">
      <!-- Hero Section -->
      <section class="py-20 px-6 flex flex-col items-center justify-center text-center">
        <h1 class="text-4xl md:text-5xl lg:text-6xl font-bold mb-2">
          Notulen
        </h1>
        <p class="text-lg md:text-xl text-muted-foreground max-w-3xl mb-10">
          Meeting notes made simple.
        </p>
        
        <div class="flex flex-col sm:flex-row gap-4">
          <button 
            v-if="authStore.isAuthenticated"
            @click="navigateToDashboard" 
            class="px-6 py-3 rounded-md bg-primary text-primary-foreground hover:bg-primary/90 text-lg font-medium"
          >
            Go to Dashboard
          </button>
          <template v-else>
            <button 
              @click="navigateToLogin" 
              class="px-6 py-3 rounded-md bg-primary text-primary-foreground hover:bg-primary/90 text-lg font-medium"
            >
              Login
            </button>
            <button 
              @click="navigateToRegister" 
              class="px-6 py-3 rounded-md bg-secondary text-secondary-foreground hover:bg-secondary/90 text-lg font-medium"
            >
              Register
            </button>
          </template>
        </div>
      </section>
      
      <!-- Features Section -->
      <section class="py-16 px-6 bg-muted/50">
        <div class="max-w-7xl mx-auto">
          <h2 class="text-3xl font-bold text-center mb-12">Key Features</h2>
          <div class="grid md:grid-cols-3 gap-8">
            <div class="bg-card p-6 rounded-lg shadow-sm">
              <h3 class="text-xl font-semibold mb-3">Meeting Recording</h3>
              <p class="text-muted-foreground">
                Easily record your meetings directly within the app. Our system securely stores and processes your audio, making it accessible to your team members while maintaining privacy.
              </p>
            </div>
            <div class="bg-card p-6 rounded-lg shadow-sm">
              <h3 class="text-xl font-semibold mb-3">AI Summarization</h3>
              <p class="text-muted-foreground">
                Transform long meetings into concise, structured summaries. Our AI automatically identifies key discussion points, decisions, and extracts actionable items for efficient follow-up.
              </p>
            </div>
            <div class="bg-card p-6 rounded-lg shadow-sm">
              <h3 class="text-xl font-semibold mb-3">Intelligent Assistant</h3>
              <p class="text-muted-foreground">
                Ask questions about any of your meetings through our chatbot. Get instant answers about decisions, action items, or participants without needing to search through transcripts or notes.
              </p>
            </div>
          </div>
        </div>
      </section>
      
      <!-- How It Works Section -->
      <section class="py-16 px-6">
        <div class="max-w-7xl mx-auto">
          <h2 class="text-3xl font-bold text-center mb-12">How Notulen Works</h2>
          <div class="grid md:grid-cols-4 gap-6 text-center">
            <div class="p-4">
              <div class="w-12 h-12 flex items-center justify-center bg-primary/10 text-primary rounded-full mx-auto mb-4">
                <span class="font-bold">1</span>
              </div>
              <h3 class="font-medium mb-2">Record</h3>
              <p class="text-sm text-muted-foreground">Record your meetings or upload existing audio files</p>
            </div>
            <div class="p-4">
              <div class="w-12 h-12 flex items-center justify-center bg-primary/10 text-primary rounded-full mx-auto mb-4">
                <span class="font-bold">2</span>
              </div>
              <h3 class="font-medium mb-2">Process</h3>
              <p class="text-sm text-muted-foreground">Our AI transcribes the audio and analyzes the content</p>
            </div>
            <div class="p-4">
              <div class="w-12 h-12 flex items-center justify-center bg-primary/10 text-primary rounded-full mx-auto mb-4">
                <span class="font-bold">3</span>
              </div>
              <h3 class="font-medium mb-2">Summarize</h3>
              <p class="text-sm text-muted-foreground">Review concise summaries and clearly defined action items</p>
            </div>
            <div class="p-4">
              <div class="w-12 h-12 flex items-center justify-center bg-primary/10 text-primary rounded-full mx-auto mb-4">
                <span class="font-bold">4</span>
              </div>
              <h3 class="font-medium mb-2">Query</h3>
              <p class="text-sm text-muted-foreground">Ask the assistant questions about any meeting, anytime</p>
            </div>
          </div>
        </div>
      </section>
    </main>
    
    <footer class="py-8 px-6 bg-muted text-center">
      <p class="text-sm text-muted-foreground">
        © 2023 Notulen. All rights reserved.
      </p>
    </footer>
  </div>
</template>

<style scoped>
/* Add any component-specific styles here */
</style>
