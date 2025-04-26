<script setup lang="ts">
import { defineProps } from 'vue'

const props = defineProps<{
  groupId: string;
  currentGroup: any;
}>()
</script>

<template>
  <div class="space-y-4">
    <div class="space-y-2">
      <h2 class="text-xl font-semibold">Group Information</h2>
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
</template>
