import requests
import moviepy.editor as mp
import os
import subprocess
from urllib.parse import urlparse
import moviepy.config as mp_config
from datetime import datetime
from PIL import Image
import base64
from io import BytesIO
import random
from openai import OpenAI
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Get API key from environment variable
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise EnvironmentError("OPENAI_API_KEY not found in environment variables.")

client = OpenAI(api_key=OPENAI_API_KEY)

# Configure ImageMagick path based on environment
if os.name == 'nt':  # Windows
    mp_config.IMAGEMAGICK_BINARY = r"C:\Program Files\ImageMagick-7.1.1-Q16-HDRI\magick.exe"
else:  # Linux (Render) or other Unix-like systems
    mp_config.IMAGEMAGICK_BINARY = "magick"  # Use system-installed ImageMagick


def encode_image_to_base64(image_path):
    """Convert image to base64 for API transmission."""
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')

def analyze_image(image_path):
    """Analyze the image using GPT-4V to understand its context."""
    try:
        base64_image = encode_image_to_base64(image_path)
        response = client.chat.completions.create(
            model="gpt-4.1-mini",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": "Describe this image in detail. What's happening in it? What emotions or situations does it convey? This will be used to generate a meme caption."},
                        {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}}
                    ]
                }
            ],
            max_tokens=300
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"Error analyzing image: {e}")
        return None

def generate_meme_caption(image_analysis):
    """Generate a meme caption based on the image analysis."""
    prompt = f"""Based on this image analysis: '{image_analysis}'
Generate a funny, relatable meme caption that matches the image's context. 
The caption should be split into two parts - a top text and bottom text (but don't actually write 'top text' or 'bottom text' in the caption, just write the text itself), separated by a newline character.
Make it humorous and relevant to what's happening in the image.
IMPORTANT: Use actual newlines, not the text '\n'."""

    response = client.chat.completions.create(
        model="gpt-4",
        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ]
    )
    
    # Clean up the response text
    text = response.choices[0].message.content
    # Replace literal '\n' with actual newlines
    text = text.replace('\\n', '\n')
    # Remove any extra whitespace around newlines
    text = '\n'.join(line.strip() for line in text.split('\n'))
    return text

def get_meme_template():
    """Fetch a random meme template from Imgflip."""
    try:
        url = "https://api.imgflip.com/get_memes"
        response = requests.get(url)
        response.raise_for_status()
        
        data = response.json()
        if data['success']:
            # Get a random meme template from the list
            meme = random.choice(data['data']['memes'])
            image_url = meme['url']
            
            print(f"Fetched meme template from Imgflip: {image_url}")
            return image_url
        else:
            print("Failed to fetch meme templates from Imgflip")
            return None
            
    except Exception as e:
        print(f"Error fetching from Imgflip: {e}")
        return None

def save_image(image_url, save_directory="original_images"):
    """Download and save an image from a URL."""
    if image_url == "No image available" or not image_url:
        print("No image URL provided to download")
        return None

    try:
        # Create the save directory if it doesn't exist
        if not os.path.exists(save_directory):
            os.makedirs(save_directory)

        # Get the filename from the URL, or use a default name
        parsed_url = urlparse(image_url)
        filename = os.path.basename(parsed_url.path)
        if not filename:
            filename = "downloaded_image.jpg"

        # Ensure the filename has an extension
        if not filename.lower().endswith(('.jpg', '.jpeg', '.png', '.gif')):
            filename += ".jpg"

        # Full path where the image will be saved
        save_path = os.path.join(save_directory, filename)

        # Download the image
        response = requests.get(image_url, stream=True, timeout=10)
        response.raise_for_status()

        # Save the image to file
        with open(save_path, 'wb') as file:
            for chunk in response.iter_content(chunk_size=8192):
                file.write(chunk)

        print(f"Original image saved to: {save_path}")
        return save_path

    except requests.exceptions.RequestException as e:
        print(f"Failed to download image: {e}")
        return None
    except Exception as e:
        print(f"Error saving image: {e}")
        return None

def create_image(text, background_path):
    """Create an image with text split between top and bottom overlay on the background."""
    # Load background image
    background = mp.ImageClip(background_path)

    # Split the text into top and bottom parts
    parts = text.split('\n')
    top_text = parts[0] if len(parts) > 0 else ""
    bottom_text = parts[1] if len(parts) > 1 else ""

    # Create top text clip with meme-style formatting
    top_text_clip = mp.TextClip(
        top_text,
        fontsize=70,
        color="white",
        stroke_color="black",
        stroke_width=2,
        font="Impact",
        size=(background.w, None)
    ).set_position(("center", 50))

    # Create bottom text clip with meme-style formatting
    bottom_text_clip = mp.TextClip(
        bottom_text,
        fontsize=70,
        color="white",
        stroke_color="black",
        stroke_width=2,
        font="Impact",
        size=(background.w, None)
    ).set_position(("center", background.h - 150))

    # Combine background and text clips
    final_image = mp.CompositeVideoClip([background, top_text_clip, bottom_text_clip])
    
    # Generate timestamp for unique filename
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Create final_images directory if it doesn't exist
    final_dir = "final_images"
    if not os.path.exists(final_dir):
        os.makedirs(final_dir)
        
    image_path = f"{final_dir}/meme_{timestamp}.jpg"
    
    # Get the frame and convert to RGB
    frame = final_image.get_frame(0)
    frame_rgb = frame[:, :, :3]  # Remove alpha channel
    
    # Save the image
    Image.fromarray(frame_rgb).save(image_path)
    print(f"Final meme saved to: {image_path}")
    return image_path

def review_video(video_path):
    """Open the video for review and get approval."""
    # Open the video (Windows example; use 'open' on macOS or 'xdg-open' on Linux)
    subprocess.run(["start", video_path], shell=True)
    approval = input("Do you want to post this video? (yes/no): ").lower()
    return approval == "yes"

def main():
    # Step 1: Get meme template
    image_url = get_meme_template()
    
    if image_url:
        saved_image_path = save_image(image_url, save_directory="original_images")
        if saved_image_path:
            print(f"Original meme template saved at: {saved_image_path}")
            
            # Step 2: Analyze the image
            print("Analyzing image...")
            image_analysis = analyze_image(saved_image_path)
            if image_analysis:
                print(f"Image analysis: {image_analysis}")
                
                # Step 3: Generate context-aware meme caption
                text = generate_meme_caption(image_analysis)
                print(f"Generated caption: {text}")
                
                # Step 4: Create meme with the template and caption
                image_path = create_image(text, saved_image_path)
                print(f"Final meme saved at: {image_path}")
                return image_path
            else:
                print("Failed to analyze image")
    else:
        print("No meme template could be found")

if __name__ == "__main__":
    main()