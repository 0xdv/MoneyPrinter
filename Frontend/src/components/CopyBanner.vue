<script setup lang="ts">
const { text } = defineProps(['text'])

function copyToClipboard() {
  navigator.clipboard.writeText(text)
}
</script>

<template>
  <q-banner rounded inline-actions class="bg-grey-2 q-ma-sm">
    {{ text }}
    <template v-slot:action>
      <q-btn flat round icon="content_copy" @click="copyToClipboard" />
    </template>
  </q-banner>
</template>

