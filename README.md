# AI Meme Generator

A web application that generates memes using AI. The application uses GPT-4 Vision to analyze images and generate contextually relevant captions.

## Features

- Fetches random meme templates from Imgflip
- Analyzes images using GPT-4 Vision
- Generates contextually relevant captions
- Creates memes with top and bottom text
- Web interface for easy meme generation
- Download generated memes

## Setup

1. Clone the repository:
```bash
git clone https://github.com/yourusername/meme-generator.git
cd meme-generator
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set up your OpenAI API key:
   - Create a `.env` file in the project root
   - Add your OpenAI API key: `OPENAI_API_KEY=your_api_key_here`

4. Run the application:
```bash
python app.py
```

5. Open your browser and go to `http://localhost:5000`

## Requirements

- Python 3.8+
- Flask
- OpenAI API key
- ImageMagick (for image processing)

## Project Structure

- `app.py` - Flask web application
- `autoposter.py` - Core meme generation logic
- `templates/` - HTML templates
- `static/` - Static files (CSS, JS)
- `original_images/` - Downloaded meme templates
- `final_images/` - Generated memes

## Contributing

Feel free to submit issues and enhancement requests!
