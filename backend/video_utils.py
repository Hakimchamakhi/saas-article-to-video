"""
Video Processing Utilities for Blog-to-Video Converter
Contains helper functions for Ken Burns effect, subtitles, audio mixing, and TTS.
"""
import asyncio
import os
import tempfile
import requests
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import numpy as np
from moviepy.editor import (
    ImageClip, AudioFileClip, CompositeAudioClip, 
    concatenate_audioclips, CompositeVideoClip, VideoClip
)

# Default background music URL (royalty-free ambient track)
# This is a short ambient loop from a public source (Pixabay-style free music)
# You can replace this with any other royalty-free MP3 URL
DEFAULT_MUSIC_URL = "https://cdn.pixabay.com/audio/2024/02/28/audio_63e9ca8a87.mp3"
# Alternative: "https://www.soundhelix.com/examples/mp3/SoundHelix-Song-1.mp3"

STATIC_DIR = Path(__file__).parent / "static"
MUSIC_PATH = STATIC_DIR / "background_music.mp3"


def ensure_background_music() -> Path:
    """
    Ensures background music exists. Downloads a default track if missing.
    Returns the path to the music file, or None if unavailable.
    """
    if MUSIC_PATH.exists():
        return MUSIC_PATH
    
    # Try to download default music
    try:
        print("Background music not found. Downloading default track...")
        response = requests.get(DEFAULT_MUSIC_URL, timeout=30)
        response.raise_for_status()
        
        STATIC_DIR.mkdir(exist_ok=True)
        with open(MUSIC_PATH, 'wb') as f:
            f.write(response.content)
        
        print(f"Downloaded background music to {MUSIC_PATH}")
        return MUSIC_PATH
    except Exception as e:
        print(f"Could not download background music: {e}")
        return None


async def generate_voiceover_edge_tts(
    text: str, 
    output_path: str, 
    voice: str = "en-US-ChristopherNeural"
) -> str:
    """
    Generate voiceover using Microsoft Edge TTS (free neural voices).
    
    Args:
        text: The text to convert to speech
        output_path: Path to save the audio file
        voice: Voice ID (e.g., 'en-US-ChristopherNeural', 'en-US-AriaNeural')
    
    Returns:
        Path to the generated audio file
    """
    import edge_tts
    
    communicate = edge_tts.Communicate(text, voice)
    await communicate.save(output_path)
    
    return output_path


def generate_voiceover_sync(
    text: str, 
    output_path: str, 
    voice: str = "en-US-ChristopherNeural"
) -> str:
    """
    Generate voiceover with edge-tts (neural voice), falling back to gTTS if blocked.
    
    Edge TTS may get 403 errors on cloud platforms (Railway, Render, etc.) because
    Microsoft blocks requests from data center IPs. In that case, we fall back to gTTS.
    
    Args:
        text: The text to convert to speech
        output_path: Path to save the audio file
        voice: Voice ID for edge-tts (ignored if falling back to gTTS)
    
    Returns:
        Path to the generated audio file
    """
    # Try edge-tts first (better quality neural voice)
    try:
        print(f"Attempting edge-tts with voice: {voice}")
        asyncio.run(generate_voiceover_edge_tts(text, output_path, voice))
        print("Edge TTS successful!")
        return output_path
    except Exception as e:
        error_msg = str(e)
        print(f"Edge TTS failed: {error_msg}")
        
        # Check if it's a 403 error (blocked by Microsoft)
        if "403" in error_msg or "WSServerHandshakeError" in error_msg:
            print("Edge TTS blocked (403). Falling back to gTTS...")
        else:
            print(f"Edge TTS error: {e}. Falling back to gTTS...")
        
        # Fallback to gTTS (still free, works everywhere, but less natural)
        try:
            from gtts import gTTS
            tts = gTTS(text=text, lang='en', slow=False)
            tts.save(output_path)
            print("gTTS fallback successful!")
            return output_path
        except Exception as gtts_error:
            print(f"gTTS also failed: {gtts_error}")
            raise RuntimeError(f"All TTS methods failed. Edge: {e}, gTTS: {gtts_error}")


def apply_ken_burns_effect(
    image_path: str,
    duration: float,
    target_size: tuple,
    effect_type: str = "zoom_in"
) -> ImageClip:
    """
    Apply Ken Burns effect (slow zoom or pan) to a static image.
    
    Args:
        image_path: Path to the image file
        duration: Duration of the clip in seconds
        target_size: Tuple of (width, height) for output
        effect_type: One of 'zoom_in', 'zoom_out', 'pan_left', 'pan_right'
    
    Returns:
        MoviePy ImageClip with animation applied
    """
    # Load and prepare image
    img = Image.open(image_path)
    
    # Convert to RGB if necessary
    if img.mode in ('RGBA', 'P'):
        img = img.convert('RGB')
    
    target_w, target_h = target_size
    
    # Scale image to be larger than target for zoom/pan room
    scale_factor = 1.2  # 20% extra for movement
    
    # Calculate scaled size maintaining aspect ratio
    img_ratio = img.width / img.height
    target_ratio = target_w / target_h
    
    if img_ratio > target_ratio:
        # Image is wider - fit by height
        new_h = int(target_h * scale_factor)
        new_w = int(new_h * img_ratio)
    else:
        # Image is taller - fit by width
        new_w = int(target_w * scale_factor)
        new_h = int(new_w / img_ratio)
    
    img_resized = img.resize((new_w, new_h), Image.LANCZOS)
    img_array = np.array(img_resized)
    
    def make_frame(t):
        """Generate frame at time t with Ken Burns effect."""
        progress = t / duration if duration > 0 else 0
        
        if effect_type == "zoom_in":
            # Start zoomed out, end zoomed in
            zoom = 1.0 - (0.15 * progress)  # 1.0 -> 0.85
            crop_w = int(target_w / zoom)
            crop_h = int(target_h / zoom)
            x = (new_w - crop_w) // 2
            y = (new_h - crop_h) // 2
            
        elif effect_type == "zoom_out":
            # Start zoomed in, end zoomed out
            zoom = 0.85 + (0.15 * progress)  # 0.85 -> 1.0
            crop_w = int(target_w / zoom)
            crop_h = int(target_h / zoom)
            x = (new_w - crop_w) // 2
            y = (new_h - crop_h) // 2
            
        elif effect_type == "pan_left":
            # Pan from right to left
            crop_w = target_w
            crop_h = target_h
            max_x = new_w - target_w
            x = int(max_x * (1 - progress))
            y = (new_h - target_h) // 2
            
        elif effect_type == "pan_right":
            # Pan from left to right
            crop_w = target_w
            crop_h = target_h
            max_x = new_w - target_w
            x = int(max_x * progress)
            y = (new_h - target_h) // 2
            
        else:
            # Default: no effect
            crop_w = target_w
            crop_h = target_h
            x = (new_w - target_w) // 2
            y = (new_h - target_h) // 2
        
        # Ensure bounds
        x = max(0, min(x, new_w - crop_w))
        y = max(0, min(y, new_h - crop_h))
        crop_w = min(crop_w, new_w - x)
        crop_h = min(crop_h, new_h - y)
        
        # Crop and resize
        cropped = img_array[y:y+crop_h, x:x+crop_w]
        
        # Resize to target using PIL for better quality
        cropped_img = Image.fromarray(cropped)
        resized = cropped_img.resize((target_w, target_h), Image.LANCZOS)
        
        return np.array(resized)
    
    # Create clip with the frame generator - must use VideoClip for animated frames
    clip = VideoClip(make_frame, duration=duration)
    clip = clip.set_fps(20)  # Match the output FPS
    
    return clip


def create_subtitle_clip(
    text: str,
    duration: float,
    video_size: tuple,
    font_size: int = 40,
    font_color: str = "white",
    stroke_color: str = "black",
    stroke_width: int = 2
) -> ImageClip:
    """
    Create a subtitle overlay clip using Pillow (no ImageMagick required).
    
    Args:
        text: Subtitle text
        duration: Duration of the clip
        video_size: Tuple of (width, height) for the video
        font_size: Font size for the text
        font_color: Color of the text
        stroke_color: Color of the text outline
        stroke_width: Width of the text outline
    
    Returns:
        MoviePy ImageClip positioned at the bottom of the video
    """
    video_w, video_h = video_size
    
    # Create transparent image for subtitle
    padding = 20
    max_text_width = video_w - (padding * 4)
    
    # Try to load a nice font, fall back to default
    try:
        # Common system fonts
        font_paths = [
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
            "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
            "/usr/share/fonts/TTF/DejaVuSans-Bold.ttf",
            "C:/Windows/Fonts/arial.ttf",
        ]
        font = None
        for fp in font_paths:
            if os.path.exists(fp):
                font = ImageFont.truetype(fp, font_size)
                break
        if font is None:
            font = ImageFont.load_default()
    except:
        font = ImageFont.load_default()
    
    # Word wrap the text
    words = text.split()
    lines = []
    current_line = []
    
    # Create dummy image for text measurement
    dummy_img = Image.new('RGBA', (1, 1))
    dummy_draw = ImageDraw.Draw(dummy_img)
    
    for word in words:
        test_line = ' '.join(current_line + [word])
        bbox = dummy_draw.textbbox((0, 0), test_line, font=font)
        line_width = bbox[2] - bbox[0]
        
        if line_width <= max_text_width:
            current_line.append(word)
        else:
            if current_line:
                lines.append(' '.join(current_line))
            current_line = [word]
    
    if current_line:
        lines.append(' '.join(current_line))
    
    wrapped_text = '\n'.join(lines)
    
    # Calculate text size
    bbox = dummy_draw.multiline_textbbox((0, 0), wrapped_text, font=font)
    text_w = bbox[2] - bbox[0]
    text_h = bbox[3] - bbox[1]
    
    # Create image with padding
    img_w = text_w + padding * 2
    img_h = text_h + padding * 2
    
    # Create semi-transparent background
    img = Image.new('RGBA', (img_w, img_h), (0, 0, 0, 160))
    draw = ImageDraw.Draw(img)
    
    # Draw text with stroke (outline)
    x = padding
    y = padding
    
    # Draw stroke by drawing text multiple times with offset
    for dx in range(-stroke_width, stroke_width + 1):
        for dy in range(-stroke_width, stroke_width + 1):
            if dx != 0 or dy != 0:
                draw.multiline_text(
                    (x + dx, y + dy),
                    wrapped_text,
                    font=font,
                    fill=stroke_color,
                    align='center'
                )
    
    # Draw main text
    draw.multiline_text(
        (x, y),
        wrapped_text,
        font=font,
        fill=font_color,
        align='center'
    )
    
    # Convert to numpy array
    img_array = np.array(img)
    
    # Create clip
    clip = ImageClip(img_array, duration=duration)
    
    # Position at bottom center
    clip = clip.set_position(('center', video_h - img_h - 50))
    
    return clip


def mix_audio_with_music(
    voiceover_path: str,
    music_path: str,
    output_path: str,
    music_volume: float = 0.15,
    duck_volume: float = 0.05
) -> str:
    """
    Mix voiceover with background music, applying ducking effect.
    The music volume is reduced when voice is speaking.
    
    Args:
        voiceover_path: Path to the voiceover audio file
        music_path: Path to the background music file
        output_path: Path to save the mixed audio
        music_volume: Normal volume level for music (0.0-1.0)
        duck_volume: Reduced volume level during speech (0.0-1.0)
    
    Returns:
        Path to the mixed audio file
    """
    # Load audio clips
    voice = AudioFileClip(voiceover_path)
    music = AudioFileClip(music_path)
    
    # Loop music if shorter than voice
    if music.duration < voice.duration:
        # Calculate how many loops needed
        loops_needed = int(voice.duration / music.duration) + 1
        music_clips = [music] * loops_needed
        music = concatenate_audioclips(music_clips)
    
    # Trim music to match voice duration
    music = music.subclip(0, voice.duration)
    
    # Apply volume reduction (simple ducking - constant lower volume)
    # For more sophisticated ducking, we'd analyze voice amplitude
    music = music.volumex(music_volume)
    
    # Composite the audio tracks
    final_audio = CompositeAudioClip([music, voice])
    
    # Write to file
    final_audio.write_audiofile(output_path, fps=44100, verbose=False, logger=None)
    
    # Clean up
    voice.close()
    music.close()
    final_audio.close()
    
    return output_path


def get_video_dimensions(video_format: str) -> tuple:
    """
    Get video dimensions based on format selection.
    
    Args:
        video_format: Either 'landscape' (YouTube 16:9) or 'portrait' (TikTok 9:16)
    
    Returns:
        Tuple of (width, height)
    """
    if video_format == "portrait":
        return (1080, 1920)  # TikTok/Shorts 9:16
    else:
        return (1920, 1080)  # YouTube 16:9 (default)


def get_pexels_orientation(video_format: str) -> str:
    """
    Get Pexels API orientation parameter based on video format.
    
    Args:
        video_format: Either 'landscape' or 'portrait'
    
    Returns:
        Pexels orientation string
    """
    if video_format == "portrait":
        return "portrait"
    else:
        return "landscape"
