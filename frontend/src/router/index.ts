import { createRouter, createWebHistory } from 'vue-router'
import InboxView from '@/views/InboxView.vue'
import LoginView from '@/views/LoginView.vue'
import RegisterView from '@/views/RegisterView.vue'
import ProfileView from '@/views/ProfileView.vue'
import { useAuthStore } from '@/stores/auth'
import AppView from '@/views/AppView.vue'
import HomeView from '@/views/HomeView.vue'
import DashboardView from '@/views/DashboardView.vue'
import GroupMainContainer from '@/containers/GroupMainContainer.vue'
import RecordContainer from '@/containers/RecordContainer.vue'
import MeetingDetailsContainer from '@/containers/MeetingDetailsContainer.vue'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/',
      name: 'home',
      component: HomeView
    },
    {
      path: '/app',
      name: 'app',
      component: AppView,
      redirect: '/dashboard',
      children: [
        {
            path: '/dashboard',
            name: 'dashboard',
            component: DashboardView,
            meta: { requiresAuth: true }
          },
        {
            path: '/inbox',
            name: 'inbox',
            component: InboxView,
            meta: { requiresAuth: true }
          },
          {
            path: '/profile',
            name: 'profile',
            component: ProfileView,
            meta: { requiresAuth: true }
          },
          {
            path: '/groups/:groupId',
            name: 'group-details',
            component: GroupMainContainer,
            meta: { requiresAuth: true }
          },
          {
            path: '/groups/:groupId/record',
            name: 'group-record',
            component: RecordContainer,
            meta: { requiresAuth: true }
          },
          {
            path: '/groups/:groupId/meetings/:meetingId',
            name: 'meeting-details',
            component: MeetingDetailsContainer,
            meta: { requiresAuth: true }
          }
      ]
    },
    {
      path: '/login',
      name: 'login',
      component: LoginView,
      meta: { guestOnly: true }
    },
    {
      path: '/register',
      name: 'register',
      component: RegisterView,
      meta: { guestOnly: true }
    }
  ]
})

// Navigation guards
router.beforeEach(async (to, _, next) => {
  const authStore = useAuthStore()
  
  // Initialize auth if not already done
  if (!authStore.user && !authStore.loading) {
    await authStore.initialize()
  }
  
  // Wait for auth to initialize
  if (authStore.loading) {
    // You might want to show a loading screen here
    // For now, we'll just wait a bit and check again
    await new Promise(resolve => setTimeout(resolve, 500))
    
    // If still loading after waiting, proceed anyway
    // The navigation guard will run again if needed once auth is initialized
    if (authStore.loading) {
      console.log('Auth still loading, proceeding with navigation')
    }
  }
  
  const requiresAuth = to.matched.some(record => record.meta.requiresAuth)
  const guestOnly = to.matched.some(record => record.meta.guestOnly)
  
  if (requiresAuth && !authStore.isAuthenticated) {
    // Redirect to login if trying to access a protected route
    next({ name: 'login', query: { redirect: to.fullPath } })
  } else if (guestOnly && authStore.isAuthenticated) {
    // Redirect to app if trying to access a guest-only route while authenticated
    next({ name: 'app' })
  } else {
    next()
  }
})

export default router 