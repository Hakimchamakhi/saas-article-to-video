"""
Celery Worker for Blog-to-Video Conversion
Handles the async video generation task with all processing steps.
"""
from celery import Celery, Task
from celery.utils.log import get_task_logger
import os
import json
import requests
import tempfile
import random
import string
from pathlib import Path
from dotenv import load_dotenv

# Third-party libraries
from newspaper import Article
from groq import Groq
from moviepy.editor import AudioFileClip, CompositeVideoClip, concatenate_videoclips

# Local utilities
from video_utils import (
    generate_voiceover_sync,
    apply_ken_burns_effect,
    create_subtitle_clip,
    mix_audio_with_music,
    ensure_background_music,
    get_video_dimensions,
    get_pexels_orientation
)

# Load environment variables
load_dotenv()

# Configure Redis URL with SSL support
redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")

# If using rediss:// (SSL), add SSL parameters
broker_use_ssl = None
if redis_url.startswith("rediss://"):
    import ssl
    broker_use_ssl = {
        'ssl_cert_reqs': ssl.CERT_NONE
    }

# Configure Celery
celery_app = Celery(
    "video_generator",
    broker=redis_url,
    backend=redis_url
)

celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    task_track_started=True,
    broker_use_ssl=broker_use_ssl,
    redis_backend_use_ssl=broker_use_ssl,
)

logger = get_task_logger(__name__)

# Initialize Groq client (FREE API)
groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))

# Pexels API configuration
PEXELS_API_KEY = os.getenv("PEXELS_API_KEY")
PEXELS_PHOTO_SEARCH_URL = "https://api.pexels.com/v1/search"

# Static directory for generated videos
STATIC_DIR = Path(__file__).parent / "static"
STATIC_DIR.mkdir(exist_ok=True)


def generate_random_filename():
    """Generate a random filename for the output video"""
    random_str = ''.join(random.choices(string.ascii_lowercase + string.digits, k=8))
    return f"video_{random_str}.mp4"


class VideoGenerationTask(Task):
    """Custom task class with progress tracking"""

    def update_progress(self, message, percentage=0, current_step="", total_steps=5):
        """Update task progress with detailed information"""
        logger.info(f"[{percentage}%] {message}")
        self.update_state(
            state='PROGRESS',
            meta={
                'progress': message,
                'percentage': percentage,
                'current_step': current_step,
                'total_steps': total_steps
            }
        )


@celery_app.task(bind=True, base=VideoGenerationTask, name="generate_video_task")
def generate_video_task(self, url: str, video_format: str = "landscape"):
    """
    Main task to generate a video from a blog article URL.

    Args:
        url: The blog article URL to convert
        video_format: 'landscape' (YouTube 16:9) or 'portrait' (TikTok 9:16)

    Steps:
    1. Scrape the article text
    2. Generate a video script using AI (Groq)
    3. Generate voiceover using Edge TTS (neural voices)
    4. Download stock images from Pexels
    5. Assemble final video with Ken Burns effect, subtitles, and background music
    6. Return the video URL
    """
    temp_files = []  # Track temporary files for cleanup

    try:
        # Step 1: Scrape the article
        self.update_progress(
            message="Scraping article content...",
            percentage=10,
            current_step="Step 1 of 5: Scraping article",
            total_steps=5
        )
        logger.info(f"Scraping article from URL: {url}")

        article = Article(url)
        article.download()
        article.parse()
        article_text = article.text

        if not article_text or len(article_text) < 100:
            raise ValueError("Article text is too short or empty. Please provide a valid article URL.")

        logger.info(f"Successfully scraped article. Length: {len(article_text)} characters")

        # Step 2: Generate video script using Groq (FREE API)
        self.update_progress(
            message="Generating video script with AI...",
            percentage=30,
            current_step="Step 2 of 5: Generating script",
            total_steps=5
        )
        logger.info("Calling Groq API to generate script...")

        script_prompt = f"""You are a video scriptwriter. Summarize the following article into a short video script. The script must be a JSON array of objects, where each object has two keys: 'scene_text' (a 1-2 sentence narration for that scene) and 'search_keyword' (a 2-3 word keyword for finding stock footage for that scene).

Create EXACTLY 3 scenes that capture the key points of the article (not more, to keep the video short and memory-efficient).

Example Response:
[
  {{"scene_text": "A new study reveals that honeybees are communicating in complex new ways.", "search_keyword": "honeybees flying"}},
  {{"scene_text": "Researchers found they use a 'waggle dance' to describe food locations with pinpoint accuracy.", "search_keyword": "bee dance research"}}
]

Article Text:
{article_text[:4000]}

Respond ONLY with the JSON array, no additional text."""

        response = groq_client.chat.completions.create(
            model="llama-3.3-70b-versatile",  # Free Groq model (updated)
            messages=[
                {"role": "system", "content": "You are a professional video scriptwriter. Always respond with valid JSON only."},
                {"role": "user", "content": script_prompt}
            ],
            temperature=0.7,
        )

        script_text = response.choices[0].message.content.strip()

        # Clean up markdown code blocks if present
        if script_text.startswith("```json"):
            script_text = script_text[7:]
        if script_text.startswith("```"):
            script_text = script_text[3:]
        if script_text.endswith("```"):
            script_text = script_text[:-3]
        script_text = script_text.strip()

        # Parse the JSON script
        try:
            script_scenes = json.loads(script_text)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse script JSON: {script_text}")
            raise ValueError(f"OpenAI returned invalid JSON: {str(e)}")

        if not isinstance(script_scenes, list) or len(script_scenes) == 0:
            raise ValueError("Script must be a non-empty array of scenes")

        logger.info(f"Generated script with {len(script_scenes)} scenes")

        # Step 3: Generate voiceover using Edge TTS (FREE Neural Voices)
        self.update_progress(
            message="Generating AI voiceover...",
            percentage=50,
            current_step="Step 3 of 5: Creating voiceover",
            total_steps=5
        )
        logger.info("Generating voiceover with Edge TTS (neural voice)...")

        # Combine all scene texts into one narration
        full_narration = " ".join([scene["scene_text"] for scene in script_scenes])

        # Generate TTS audio using Edge TTS (human-like neural voice)
        voiceover_path = tempfile.NamedTemporaryFile(delete=False, suffix=".mp3").name
        temp_files.append(voiceover_path)

        # Use Microsoft Edge neural voice
        generate_voiceover_sync(
            text=full_narration,
            output_path=voiceover_path,
            voice="en-US-ChristopherNeural"  # Male neural voice
        )

        logger.info(f"Voiceover saved to {voiceover_path}")

        # Step 4: Download stock video clips
        self.update_progress(
            message="Finding and downloading stock footage...",
            percentage=65,
            current_step="Step 4 of 5: Downloading stock footage",
            total_steps=5
        )
        logger.info("Downloading stock videos from Pexels...")

        video_clips_paths = []

        # Load voiceover to get duration
        audio_clip = AudioFileClip(voiceover_path)
        audio_duration = audio_clip.duration
        logger.info(f"Audio duration: {audio_duration} seconds")

        # Calculate duration per scene
        duration_per_scene = audio_duration / len(script_scenes)

        # Get orientation based on video format
        pexels_orientation = get_pexels_orientation(video_format)
        video_dimensions = get_video_dimensions(video_format)
        logger.info(f"Video format: {video_format}, dimensions: {video_dimensions}")

        for idx, scene in enumerate(script_scenes):
            keyword = scene["search_keyword"]
            logger.info(f"Searching Pexels for: {keyword}")

            # Search Pexels for photos (images use much less memory than videos)
            headers = {"Authorization": PEXELS_API_KEY}
            params = {
                "query": keyword,
                "per_page": 5,
                "orientation": pexels_orientation
            }

            try:
                pexels_response = requests.get(
                    PEXELS_PHOTO_SEARCH_URL,
                    headers=headers,
                    params=params,
                    timeout=10
                )
                pexels_response.raise_for_status()
                pexels_data = pexels_response.json()

                if pexels_data.get("photos") and len(pexels_data["photos"]) > 0:
                    # Get the first photo
                    photo = pexels_data["photos"][0]

                    # Use medium-sized image for optimal memory/quality balance
                    image_url = photo["src"].get("large") or photo["src"].get("original")

                    if image_url:
                        logger.info(f"Downloading image from: {image_url}")

                        # Download the image
                        image_response = requests.get(image_url, timeout=30)
                        image_response.raise_for_status()

                        # Save to temporary file
                        image_path = tempfile.NamedTemporaryFile(delete=False, suffix=".jpg").name
                        temp_files.append(image_path)

                        with open(image_path, 'wb') as f:
                            f.write(image_response.content)

                        video_clips_paths.append(image_path)
                        logger.info(f"Downloaded image {idx + 1}/{len(script_scenes)}")
                    else:
                        logger.warning(f"No image URL found for keyword: {keyword}")
                else:
                    logger.warning(f"No photos found for keyword: {keyword}")

            except Exception as e:
                logger.error(f"Error downloading image for '{keyword}': {str(e)}")
                # Continue even if one clip fails

        if len(video_clips_paths) == 0:
            raise ValueError("Could not download any stock images. Please check your Pexels API key.")

        logger.info(f"Successfully downloaded {len(video_clips_paths)} images")

        # Step 5: Assemble the final video
        self.update_progress(
            message="Assembling final video...",
            percentage=85,
            current_step="Step 5 of 5: Assembling final video",
            total_steps=5
        )
        logger.info("Assembling video with MoviePy...")

        # Ken Burns effect types to randomly apply
        ken_burns_effects = ["zoom_in", "zoom_out", "pan_left", "pan_right"]

        # Process images with Ken Burns effect and subtitles
        scene_clips = []
        for idx, image_path in enumerate(video_clips_paths):
            try:
                logger.info(f"Processing image {idx + 1}/{len(video_clips_paths)} with Ken Burns effect")
                
                # Apply random Ken Burns effect
                effect_type = random.choice(ken_burns_effects)
                clip = apply_ken_burns_effect(
                    image_path=image_path,
                    duration=duration_per_scene,
                    target_size=video_dimensions,
                    effect_type=effect_type
                )
                
                # Create subtitle for this scene
                scene_text = script_scenes[idx]["scene_text"] if idx < len(script_scenes) else ""
                if scene_text:
                    subtitle = create_subtitle_clip(
                        text=scene_text,
                        duration=duration_per_scene,
                        video_size=video_dimensions,
                        font_size=36 if video_format == "portrait" else 40
                    )
                    # Composite the subtitle over the image
                    clip = CompositeVideoClip([clip, subtitle])
                
                scene_clips.append(clip)
            except Exception as e:
                logger.error(f"Error processing image {image_path}: {str(e)}")

        if len(scene_clips) == 0:
            raise ValueError("Could not process any image clips")

        # Concatenate all scene clips
        visual_track = concatenate_videoclips(scene_clips, method="compose")

        # Mix voiceover with background music (if available)
        final_audio_path = voiceover_path
        music_path = ensure_background_music()
        
        if music_path and music_path.exists():
            logger.info("Mixing voiceover with background music...")
            try:
                mixed_audio_path = tempfile.NamedTemporaryFile(delete=False, suffix=".mp3").name
                temp_files.append(mixed_audio_path)
                
                mix_audio_with_music(
                    voiceover_path=voiceover_path,
                    music_path=str(music_path),
                    output_path=mixed_audio_path,
                    music_volume=0.12,
                    duck_volume=0.05
                )
                final_audio_path = mixed_audio_path
                logger.info("Audio mixed successfully")
            except Exception as e:
                logger.warning(f"Could not mix background music: {e}. Using voiceover only.")
        else:
            logger.info("No background music available, using voiceover only")

        # Set the final audio
        final_audio = AudioFileClip(final_audio_path)
        final_video = visual_track.set_audio(final_audio)

        # Generate output filename
        output_filename = generate_random_filename()
        output_path = STATIC_DIR / output_filename

        logger.info(f"Writing final video to {output_path}")

        # Write the final video with highly optimized settings for free tier (512MB RAM limit)
        final_video.write_videofile(
            str(output_path),
            codec="libx264",
            audio_codec="aac",
            audio_bitrate='96k',  # Lower audio bitrate to save memory
            temp_audiofile=tempfile.NamedTemporaryFile(delete=False, suffix=".m4a").name,
            remove_temp=True,
            fps=20,  # Lower FPS = less frames to process
            preset='ultrafast',  # Fastest encoding, less memory
            threads=1,  # Single thread to minimize memory usage
            bitrate='500k',  # Very low bitrate for smaller file size and less memory
            logger=None,  # Disable verbose logging to reduce overhead
            write_logfile=False  # Don't write log file
        )

        # Clean up MoviePy clips to free memory
        audio_clip.close()
        final_audio.close()
        for clip in scene_clips:
            clip.close()
        visual_track.close()
        final_video.close()

        logger.info(f"Video generation complete: {output_filename}")

        # Return success result
        return {
            "status": "success",
            "video_filename": output_filename,
            "message": "Video generated successfully"
        }

    except Exception as e:
        logger.error(f"Error in video generation task: {str(e)}", exc_info=True)
        # Re-raise the exception so Celery marks the task as FAILED
        raise

    finally:
        # Clean up temporary files
        for temp_file in temp_files:
            try:
                if os.path.exists(temp_file):
                    os.remove(temp_file)
                    logger.info(f"Cleaned up temporary file: {temp_file}")
            except Exception as e:
                logger.warning(f"Could not delete temporary file {temp_file}: {str(e)}")
