import requests
import os
from urllib.parse import urlparse
from datetime import datetime
from PIL import Image, ImageDraw, ImageFont
from io import BytesIO
import base64
import random
from openai import OpenAI

OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise EnvironmentError("OPENAI_API_KEY not found. Set it as an environment variable.")

client = OpenAI(api_key=OPENAI_API_KEY)


def encode_image_to_base64(image_path):
    """Convert image to base64 for API transmission."""
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')


def analyze_image(image_path):
    """Analyze the image using GPT-4 vision to understand its context."""
    try:
        base64_image = encode_image_to_base64(image_path)
        response = client.chat.completions.create(
            model="gpt-4.1-mini",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": (
                                "Describe this image in detail. What's happening in it? "
                                "What emotions or situations does it convey? "
                                "This will be used to generate a meme caption."
                            )
                        },
                        {
                            "type": "image_url",
                            "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}
                        }
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
    prompt = (
        f"Based on this image analysis: '{image_analysis}'\n"
        "Generate a dark, relatable meme caption that matches the image's context.\n"
        "The caption should be two short lines — a top line and a bottom line, separated by a newline.\n"
        "Do NOT label them 'top text' or 'bottom text'. Just write the text.\n"
        "Keep each line concise (under 60 characters). Use actual newlines, not '\\n'."
    )

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": prompt}]
    )

    text = response.choices[0].message.content
    # Normalize literal '\n' strings to real newlines
    text = text.replace('\\n', '\n')
    # Strip each line
    text = '\n'.join(line.strip() for line in text.split('\n') if line.strip())
    return text


def get_meme_template():
    """Fetch a random meme template from Imgflip."""
    try:
        response = requests.get("https://api.imgflip.com/get_memes", timeout=10)
        response.raise_for_status()
        data = response.json()
        if data['success']:
            meme = random.choice(data['data']['memes'])
            print(f"Fetched meme template: {meme['url']}")
            return meme['url']
        print("Imgflip returned no memes")
        return None
    except Exception as e:
        print(f"Error fetching from Imgflip: {e}")
        return None


def save_image(image_url, save_directory="original_images"):
    """Download and save an image from a URL."""
    if not image_url:
        return None
    try:
        os.makedirs(save_directory, exist_ok=True)

        parsed_url = urlparse(image_url)
        filename = os.path.basename(parsed_url.path) or "template.jpg"
        if not filename.lower().endswith(('.jpg', '.jpeg', '.png', '.gif')):
            filename += ".jpg"

        save_path = os.path.join(save_directory, filename)
        response = requests.get(image_url, stream=True, timeout=10)
        response.raise_for_status()

        with open(save_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)

        print(f"Template saved to: {save_path}")
        return save_path
    except Exception as e:
        print(f"Error saving image: {e}")
        return None


def _load_impact_font(size):
    """Try to load the Impact font at the given size, falling back to default."""
    candidates = [
        "C:/Windows/Fonts/impact.ttf",
        "/usr/share/fonts/truetype/msttcorefonts/Impact.ttf",
        "/usr/share/fonts/truetype/freefont/FreeMonoBold.ttf",
        "impact.ttf",
    ]
    for path in candidates:
        try:
            return ImageFont.truetype(path, size)
        except Exception:
            pass
    return ImageFont.load_default()


def _wrap_text(draw, text, font, max_width):
    """Word-wrap text to fit within max_width pixels."""
    words = text.split()
    lines = []
    current = []
    for word in words:
        test = ' '.join(current + [word])
        bbox = draw.textbbox((0, 0), test, font=font)
        if bbox[2] - bbox[0] <= max_width:
            current.append(word)
        else:
            if current:
                lines.append(' '.join(current))
            current = [word]
    if current:
        lines.append(' '.join(current))
    return '\n'.join(lines)


def _draw_outlined_text(draw, text, x, y, font, fill="white", outline="black", outline_width=3):
    """Draw text with a solid outline for meme-style legibility."""
    for dx in range(-outline_width, outline_width + 1):
        for dy in range(-outline_width, outline_width + 1):
            if dx != 0 or dy != 0:
                draw.multiline_text((x + dx, y + dy), text, font=font, fill=outline, align="center")
    draw.multiline_text((x, y), text, font=font, fill=fill, align="center")


def create_image(text, background_path):
    """Overlay meme captions on the background image and save to final_images/."""
    img = Image.open(background_path).convert("RGB")
    width, height = img.size
    draw = ImageDraw.Draw(img)

    # Parse top/bottom text
    lines = [l.strip() for l in text.strip().split('\n') if l.strip()]
    top_text = lines[0] if len(lines) > 0 else ""
    bottom_text = lines[1] if len(lines) > 1 else ""

    font_size = max(int(height * 0.08), 28)
    font = _load_impact_font(font_size)
    padding = 20

    if top_text:
        wrapped = _wrap_text(draw, top_text, font, width - padding * 2)
        bbox = draw.multiline_textbbox((0, 0), wrapped, font=font, align="center")
        text_w = bbox[2] - bbox[0]
        x = (width - text_w) // 2
        _draw_outlined_text(draw, wrapped, x, padding, font)

    if bottom_text:
        wrapped = _wrap_text(draw, bottom_text, font, width - padding * 2)
        bbox = draw.multiline_textbbox((0, 0), wrapped, font=font, align="center")
        text_w = bbox[2] - bbox[0]
        text_h = bbox[3] - bbox[1]
        x = (width - text_w) // 2
        y = height - text_h - padding
        _draw_outlined_text(draw, wrapped, x, y, font)

    os.makedirs("final_images", exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    image_path = f"final_images/meme_{timestamp}.jpg"
    img.save(image_path, quality=95)
    print(f"Meme saved to: {image_path}")
    return image_path


def main():
    image_url = get_meme_template()
    if not image_url:
        print("No meme template could be found")
        return

    saved_image_path = save_image(image_url, save_directory="original_images")
    if not saved_image_path:
        print("Failed to save template")
        return

    print("Analyzing image...")
    image_analysis = analyze_image(saved_image_path)
    if not image_analysis:
        print("Failed to analyze image")
        return

    print(f"Analysis: {image_analysis}")
    text = generate_meme_caption(image_analysis)
    print(f"Caption: {text}")

    image_path = create_image(text, saved_image_path)
    print(f"Final meme: {image_path}")
    return image_path


if __name__ == "__main__":
    main()
