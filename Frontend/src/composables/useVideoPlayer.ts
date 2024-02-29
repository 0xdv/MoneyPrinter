import { ref } from 'vue'

export function useVideoPlayer() {
  const videoPlayer = ref<HTMLVideoElement>()

  function playVideo(event: MouseEvent) {
    (event.target as HTMLVideoElement).play()
  }

  function pauseVideo(event: MouseEvent) {
    (event.target as HTMLVideoElement).pause()
  }

  return { videoPlayer, playVideo, pauseVideo }
}