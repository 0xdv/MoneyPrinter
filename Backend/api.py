import os
import time
from termcolor import colored
from flask import Blueprint, request, jsonify, send_file
from gpt import generate_script as request_script, get_search_terms, generate_metadata
from search import search_for_stock_videos
from video import save_video
from tiktokvoice import tts
from uuid import uuid4
from moviepy.editor import concatenate_audioclips, AudioFileClip
from utils import clean_dir
from video import generate_subtitles, combine_videos, generate_video

SEARCH_TERM_COUNT = 7

api_blueprint = Blueprint('api', __name__)

@api_blueprint.route("/api/generate_script", methods=["POST"])
def generate_script():
    data = request.get_json()
    videoSubject = data.get('videoSubject')
    paragraph_number = int(data.get('paragraphNumber', 1))
    ai_model = data.get('aiModel', 'g4f')
    voice = data.get('voice', 'en_us_001')

    # Generate a script
    script = request_script(videoSubject, paragraph_number, ai_model, voice, None)  # Pass the AI model to the script generation

    # Generate search terms
    search_terms = get_search_terms(videoSubject, SEARCH_TERM_COUNT, script, ai_model)

    return jsonify(
      {
          "status": "success",
          "data": {
            "script": script,
            "search_terms": search_terms
          },
      }
    )

@api_blueprint.route("/api/search_videos", methods=["POST"])
def search_videos():
    data = request.get_json()
    # script = data.get('script')
    search_terms = data.get('search_terms')
    print(search_terms)

    # Search for a video of the given search term
    video_urls = []

    # Defines how many results it should query and search through
    count = 15

    # Defines the minimum duration of each clip
    min_dur = 10

    # Loop through all search terms,
    # and search for a video of the given search term
    for search_term in search_terms:
        found_urls = search_for_stock_videos(search_term, os.getenv("PEXELS_API_KEY"), count, min_dur)
        # Check for duplicates
        for url in found_urls:
            if url not in video_urls:
                video_urls.append(url)
                break

    # Check if video_urls is empty
    if not video_urls:
        print(colored("[-] No videos found to download.", "red"))
        return jsonify(
            {
                "status": "error",
                "message": "No videos found to download.",
                "data": [],
            }
        )

    return jsonify(
      {
          "status": "success",
          "data": {
            "video_urls": video_urls
          },
      }
    )

@api_blueprint.route("/api/create_video", methods=["POST"])
def create_video():
    start_time = time.time()

    data = request.get_json()
    script = data.get('script')
    video_urls = data.get('video_urls')

    voice = data.get('voice', 'en_us_001')

    # clean up
    clean_dir("../temp/")
    clean_dir("../subtitles/")

    # download videos
    video_paths = download_videos(video_urls)

    # combine videos
    outputPath = gener(script, voice, video_paths)
    # generate subtitles

    # Put everything together

    print(colored(f"[+] Video generated: {outputPath}!", "green"))

    # Stop FFMPEG processes
    if os.name == "nt":
        # Windows
        os.system("taskkill /f /im ffmpeg.exe")
    else:
        # Other OS
        os.system("pkill -f ffmpeg")

    end_time = time.time()
    print(colored(f"Full process took {(end_time - start_time):2f} seconds",'grey'))

    return jsonify(
      {
          "status": "success",
          "data": {
            "metadata": {
              "videoUrl": outputPath
            }
          },
      }
    )

@api_blueprint.route('/api/video')
def get_video():
    video_path = "/temp/output.mp4"
    return send_file(video_path, mimetype='video/mp4') 

@api_blueprint.route("/api/create_metadata", methods=["POST"])
def create_metadata():
    data = request.get_json()
    video_subject = data.get('video_subject')
    script = data.get('script')
    ai_model = data.get('aiModel', 'g4f')

    title, description = generate_video_metadata(video_subject, script, ai_model)

    return jsonify(
    {
        "status": "success",
        "data": {
          "metadata": {
            "title": title,
            "description": description
          }
        },
    }
  )

def download_videos(video_urls):
    video_paths = []

    print(colored(f"[+] Downloading {len(video_urls)} videos...", "blue"))

    # Save the videos
    for video_url in video_urls:
        try:
            saved_video_path = save_video(video_url)
            video_paths.append(saved_video_path)
        except Exception:
            print(colored(f"[-] Could not download video: {video_url}", "red"))

    print(colored("[+] Videos downloaded!", "green"))
    return video_paths

def gener(script, voice, video_paths):
    n_threads = 4
    subtitles_position = 'center,center'
    text_color = "#FF0000"
    voice_prefix = voice[:2]

    # Split script into sentences
    sentences = script.split(". ")
    # Remove empty strings
    sentences = list(filter(lambda x: x != "", sentences))
    
    paths = []

    # Generate TTS for every sentence
    for sentence in sentences:
        current_tts_path = f"../temp/{uuid4()}.mp3"
        tts(sentence, voice, filename=current_tts_path)
        audio_clip = AudioFileClip(current_tts_path)
        paths.append(audio_clip)

    # Combine all TTS files using moviepy
    final_audio = concatenate_audioclips(paths)
    tts_path = f"../temp/{uuid4()}.mp3"
    final_audio.write_audiofile(tts_path)

    try:
        subtitles_path = generate_subtitles(audio_path=tts_path, sentences=sentences, audio_clips=paths, voice=voice_prefix)
    except Exception as e:
        print(colored(f"[-] Error generating subtitles: {e}", "red"))
        subtitles_path = None

    # Concatenate videos
    temp_audio = AudioFileClip(tts_path)
    combined_video_path = combine_videos(video_paths, temp_audio.duration, 5, n_threads or 2)

    # Put everything together
    try:
        final_video_path = generate_video(combined_video_path, tts_path, subtitles_path, n_threads or 2, subtitles_position, text_color or "#FFFF00")
    except Exception as e:
        print(colored(f"[-] Error generating final video: {e}", "red"))
        final_video_path = None
    return final_video_path


def generate_video_metadata(video_subject, script, ai_model):
    # Define metadata for the video, we will display this to the user, and use it for the YouTube upload
    title, description, keywords = generate_metadata(video_subject, script, ai_model)

    print(colored("[-] Metadata for YouTube upload:", "blue"))
    print(colored("   Title: ", "blue"))
    print(colored(f"   {title}", "blue"))
    print(colored("   Description: ", "blue"))
    print(colored(f"   {description}", "blue"))
    print(colored("   Keywords: ", "blue"))
    print(colored(f"  {', '.join(keywords)}", "blue"))

    return title, description