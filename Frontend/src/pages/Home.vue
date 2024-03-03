<script setup lang="ts">
import { ref, computed } from 'vue'
import { useVideoPlayer } from "@/composables/useVideoPlayer"
import CopyBanner from "@/components/CopyBanner.vue"

const scriptUrl = "http://localhost:8080/api/generate_script"
const searchVideosUrl = "http://localhost:8080/api/search_videos"
const createVideoUrl = "http://localhost:8080/api/create_video"
const createMetadataUrl = "http://localhost:8080/api/create_metadata"
const requestVideoUrl = "http://localhost:8080/api/video"
const publishVideoUrl = "http://localhost:8080/api/publish_video"

interface IVideo {
  src: string,
  isDeleted: boolean
}

const subjectText = ref<string>()
const step = ref<number>(1)
const script = ref<string>()
const searchTerms = ref<string[]>()
const videoStatus = ref<string>()
const resultUrl = ref<string>()
const videoRoll = ref<IVideo[]>()

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
      videoRoll.value = response.data.video_urls.map((v: string) => ({
        src: v,
        isDeleted: false
      }))
      videoStatus.value = `Found ${response.data.video_urls.length} videos`

    } else {
      videoStatus.value = "No videos found 😔"
    }

  } catch (error) {
    alert("An error occurred. Please try again later.");
    console.log(error);
  }
}

function create() {
  createVideo()
  createMetadata()
}

async function createVideo() {
  let request = {
    video_subject: subjectText.value,
    script: script.value,
    search_terms: searchTerms.value,
    video_urls: videoRoll.value?.filter(v => !v.isDeleted).map(v => v.src)
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

const title = ref<string>()
const description = ref<string>()
const keywords = ref<string[]>()
async function createMetadata() {
  let request = {
    video_subject: subjectText.value,
    script: script.value,
  }

  try {
    let response = await fetch(createMetadataUrl, {
      method: "POST",
      body: JSON.stringify(request),
      headers: {
        "Content-Type": "application/json",
        Accept: "application/json",
      },
    }).then((response) => response.json())
    if (response.status === 'success') {
      title.value = response.data.metadata.title
      description.value = response.data.metadata.description
      keywords.value = response.data.metadata.keywords
    }

  } catch (error) {
    alert("An error occurred. Please try again later.");
    console.log(error);
  }
}

async function requestVideo() {
  step.value++

  try {
    fetch(requestVideoUrl)
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

function deleteVideo(index: number) {
  if (videoRoll.value) {
    videoRoll.value[index].isDeleted = !videoRoll.value[index].isDeleted
  }
}

type Visibility = "private" | "public"
const privacyStatus = ref<Visibility>("private");
const publishModel = ref({
  title,
  description,
  keywords,
  privacyStatus
})

async function publishVideo() {
  let request = {
    title: title.value,
    description: description.value,
    keywords: keywords.value,
    privacyStatus: privacyStatus.value
  }

  try {
    let response = await fetch(publishVideoUrl, {
      method: "POST",
      body: JSON.stringify(request),
      headers: {
        "Content-Type": "application/json",
        Accept: "application/json",
      },
    }).then((response) => response.json())
    if (response.status === 'success') {
      alert('Done')
    }

  } catch (error) {
    alert("An error occurred. Please try again later.");
    console.log(error);
  }
}
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

            <div v-if="videoRoll" class="video-roll">
              <div v-for="(video, index) in videoRoll" :key="index" class="q-ma-sm video-container">
                <video ref="videoPlayer" :class="{ 'deleted-video': video.isDeleted }" @mouseover="playVideo"
                  @mouseout="pauseVideo" volume="0">
                  <source :src="video.src" type="video/mp4" />
                </video>
                <q-btn class="delete-video-btn q-ma-sm" round icon="close" color="gray" @click="deleteVideo(index)" />
              </div>
            </div>

            <q-stepper-navigation>
              <q-btn @click="create" color="primary" label="Create Video" />
              <q-btn flat @click="step--" color="primary" label="Back" class="q-ml-sm" />
            </q-stepper-navigation>
          </q-step>

          <q-step :name="4" title="Result" icon="settings" :done="step > 4">
            <div style="display: flex">
              <div>
                <video class="q-ma-sm" :src="resultUrl" controls style="width: 300px;" volume="10"></video>
              </div>
              <div>
                <CopyBanner :text="title" />
                <CopyBanner :text="description" />
                <q-banner rounded class="bg-grey-2 q-ma-sm">
                  <q-chip v-if="keywords" v-for="kw in keywords" :key="kw" icon="tag">
                    {{ kw }}
                  </q-chip>
                </q-banner>
              </div>
            </div>

            <div class="q-pa-md">
              <q-btn-toggle v-model="privacyStatus" toggle-color="primary" :options="[
                { label: 'Private', value: 'private' },
                { label: 'Public', value: 'public' },
              ]" />
            </div>

            <q-stepper-navigation>
              <q-btn color="primary" label="Publish" @click="publishVideo" />
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
  align-items: center;
}

.video-container {
  position: relative;
  width: 200px;
  transition: transform 0.3s ease-in-out;
}

.video-container:hover {
  transform: scale(1.5);
  z-index: 90;
}

.video-container video {
  max-width: 100%;
  height: auto;
}

.deleted-video {
  filter: grayscale(100%)
}

.delete-video-btn {
  position: absolute;
  top: 0;
  right: 0;
  z-index: 99;
}
</style>