<script setup lang="ts">
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { LogIn, UserPlus, User } from 'lucide-vue-next'

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

const components: { title: string, href: string, description: string }[] = [
  {
    title: 'Alert Dialog',
    href: '/docs/components/alert-dialog',
    description:
      'A modal dialog that interrupts the user with important content and expects a response.',
  },
  {
    title: 'Hover Card',
    href: '/docs/components/hover-card',
    description:
      'For sighted users to preview content available behind a link.',
  },
  {
    title: 'Progress',
    href: '/docs/components/progress',
    description:
      'Displays an indicator showing the completion progress of a task, typically displayed as a progress bar.',
  },
  {
    title: 'Scroll-area',
    href: '/docs/components/scroll-area',
    description: 'Visually or semantically separates content.',
  },
  {
    title: 'Tabs',
    href: '/docs/components/tabs',
    description:
      'A set of layered sections of content—known as tab panels—that are displayed one at a time.',
  },
  {
    title: 'Tooltip',
    href: '/docs/components/tooltip',
    description:
      'A popup that displays information related to an element when the element receives keyboard focus or the mouse hovers over it.',
  },
]
</script>

<template>
  <div class="w-full py-4 px-6 flex items-center justify-end">
    <!-- Auth buttons -->
    <div class="flex items-center space-x-4">
      <div v-if="authStore.isAuthenticated" class="flex items-center space-x-4">
        <div class="flex items-center space-x-2">
          <div class="w-8 h-8 rounded-full bg-gray-200 dark:bg-gray-700 flex items-center justify-center">
            <User class="w-4 h-4" />
          </div>
          <span class="text-sm hidden md:inline">{{ authStore.user?.email }}</span>
        </div>
        <button 
          @click="navigateToDashboard" 
          class="px-4 py-2 rounded-md bg-primary text-primary-foreground hover:bg-primary/90 flex items-center"
        >
          <LogIn class="w-4 h-4 mr-2" />
          <span>Dashboard</span>
        </button>
      </div>
      <div v-else class="flex items-center space-x-4">
        <button 
          @click="navigateToLogin" 
          class="px-4 py-2 rounded-md bg-primary text-primary-foreground hover:bg-primary/90 flex items-center"
        >
          <LogIn class="w-4 h-4 mr-2" />
          <span>Login</span>
        </button>
        <button 
          @click="navigateToRegister" 
          class="px-4 py-2 rounded-md bg-secondary text-secondary-foreground hover:bg-secondary/90 flex items-center"
        >
          <UserPlus class="w-4 h-4 mr-2" />
          <span>Register</span>
        </button>
      </div>
    </div>
  </div>
</template>