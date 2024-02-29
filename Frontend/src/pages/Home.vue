<script setup lang="ts">
import { ref, computed } from 'vue'
import { useVideoPlayer } from "@/composables/useVideoPlayer"

const scriptUrl = "http://localhost:8080/api/generate_script";
const searchVideosUrl = "http://localhost:8080/api/search_videos";
const createVideoUrl = "http://localhost:8080/api/create_video";

const subjectText = ref<string>()
const step = ref<number>(1)
const script = ref<string>()
const searchTerms = ref<string[]>()
const videoStatus = ref<string>()
const videoUrls = ref<string[]>()
const resultUrl = ref<string>()

const disableGenerateScript = computed(() => {
  return !subjectText.value || subjectText.value === "";
})

async function generateScript() {
  step.value++

  let request = {
    videoSubject: subjectText.value
  }

  try {
    script.value = "Loading..."
    searchTerms.value = []
    let response = await fetch(scriptUrl, {
      method: "POST",
      body: JSON.stringify(request),
      headers: {
        "Content-Type": "application/json",
        Accept: "application/json",
      },
    }).then((response) => response.json())
    if (response.status === 'success') {
      script.value = response.data.script
      searchTerms.value = response.data.search_terms
    }

  } catch (error) {
    alert("An error occurred. Please try again later.");
    console.log(error);
  }
}

async function searchVideos() {
  step.value++

  videoStatus.value = "Searching videos..."
  let request = {
    scirpt: script.value,
    search_terms: searchTerms.value
    // search_terms: ["tokyo history", "tokyo culture", "tokyo modernity", "tokyo Brandenburg Gate", "tokyo street art", "tokyo tokyo Wall", "tokyo museums"]
  }

  try {
    let response = await fetch(searchVideosUrl, {
      method: "POST",
      body: JSON.stringify(request),
      headers: {
        "Content-Type": "application/json",
        Accept: "application/json",
      },
    }).then((response) => response.json())
    if (response.status === 'success' &&
      response.data &&
      response.data.video_urls &&
      response.data.video_urls.length > 0) {
      videoUrls.value = response.data.video_urls
      videoStatus.value = `Found ${response.data.video_urls.length} videos`

    } else {
      videoStatus.value = "No videos found 😔"
    }

  } catch (error) {
    alert("An error occurred. Please try again later.");
    console.log(error);
  }
}

async function createVideo() {
  // step.value++

  let request = {
    video_subject: subjectText.value,
    script: script.value,
    search_terms: searchTerms.value,
    video_urls: videoUrls.value
  }

  try {
    let response = await fetch(createVideoUrl, {
      method: "POST",
      body: JSON.stringify(request),
      headers: {
        "Content-Type": "application/json",
        Accept: "application/json",
      },
    }).then((response) => response.json())
    if (response.status === 'success') {
      requestVideo()
    }

  } catch (error) {
    alert("An error occurred. Please try again later.");
    console.log(error);
  }
}

async function requestVideo() {
  step.value++

  try {
    fetch("http://localhost:8080/api/video")
      .then((response) => response.blob())
      .then(blob => {
        resultUrl.value = URL.createObjectURL(blob);
      })
  } catch (error) {
    alert("An error occurred. Please try again later.");
    console.log(error);
  }
}

const { videoPlayer, playVideo, pauseVideo } = useVideoPlayer()
</script>

<template>
  <main>
    <q-layout>
      <q-page-container>
        <q-stepper v-model="step" vertical color="primary" animated>
          <q-step :name="1" title="Video Subject" icon="settings" :done="step > 1">
            <q-input v-model="subjectText" placeholder="type video subject here"></q-input>

            <q-stepper-navigation>
              <q-btn @click="generateScript" :disable="disableGenerateScript" color="primary" label="Generate script" />
            </q-stepper-navigation>
          </q-step>

          <q-step :name="2" title="Script" icon="create_new_folder" :done="step > 2">
            Creating script for "{{ subjectText }}"

            <q-banner rounded class="bg-grey-2">
              {{ script }}
              <br />
              <q-chip v-if="searchTerms" v-for="term in searchTerms" :key="term" icon="tag">
                {{ term }}
              </q-chip>
            </q-banner>

            <q-stepper-navigation>
              <q-btn @click="searchVideos" color="primary" label="Continue" />
              <q-btn flat @click="step--" color="primary" label="Back" class="q-ml-sm" />
            </q-stepper-navigation>
          </q-step>

          <q-step :name="3" title="Video Sequence" icon="settings" :done="step > 3">
            {{ videoStatus }}

            <div v-if="videoUrls" class="video-roll">
              <div v-for="videoUrl in videoUrls" class="q-ma-sm video-container">
                <video ref="videoPlayer" @mouseover="playVideo" @mouseout="pauseVideo" volume="0">
                  <source :src="videoUrl" type="video/mp4" />
                </video>
              </div>
            </div>

            <q-stepper-navigation>
              <q-btn @click="createVideo" color="primary" label="Create Video" />
              <q-btn flat @click="step--" color="primary" label="Back" class="q-ml-sm" />
            </q-stepper-navigation>
          </q-step>

          <q-step :name="4" title="Output" icon="settings" :done="step > 4">
            <video class="q-ma-sm" :src="resultUrl" controls style="width: 300px;"></video>

            <q-stepper-navigation>
              <q-btn color="primary" label="Good" />
              <q-btn flat @click="step--" color="primary" label="Back" class="q-ml-sm" />
            </q-stepper-navigation>
          </q-step>
        </q-stepper>
      </q-page-container>
    </q-layout>
  </main>
</template>

<style>
.video-roll {
  display: flex;
  flex-wrap: wrap;
}

.video-container {
  width: 200px;
  transition: transform 0.3s ease-in-out;
}

.video-container:hover {
  transform: scale(1.5);
  z-index: 99;
}

.video-container video {
  max-width: 100%;
  height: auto;
}
</style>