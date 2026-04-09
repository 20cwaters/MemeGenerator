from flask import Flask, render_template, jsonify, send_from_directory
import os
from autoposter import get_meme_template, save_image, analyze_image, generate_meme_caption, create_image

app = Flask(__name__)

FINAL_IMAGES_DIR = os.path.join(os.path.dirname(__file__), "final_images")


@app.route('/')
def home():
    return render_template('index.html')


@app.route('/generate-meme', methods=['POST'])
def generate_meme():
    try:
        image_url = get_meme_template()
        if not image_url:
            return jsonify({'success': False, 'error': 'Could not fetch a meme template'}), 500

        saved_image_path = save_image(image_url, save_directory="original_images")
        if not saved_image_path:
            return jsonify({'success': False, 'error': 'Could not download the template image'}), 500

        image_analysis = analyze_image(saved_image_path)
        if not image_analysis:
            return jsonify({'success': False, 'error': 'Could not analyze the image'}), 500

        text = generate_meme_caption(image_analysis)
        final_image_path = create_image(text, saved_image_path)

        filename = os.path.basename(final_image_path)
        return jsonify({'success': True, 'filename': filename})

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/meme/<filename>')
def get_meme(filename):
    """Serve a generated meme by filename (basename only — no path traversal)."""
    # Reject anything that isn't a plain filename
    if filename != os.path.basename(filename):
        return jsonify({'error': 'Invalid filename'}), 400
    return send_from_directory(FINAL_IMAGES_DIR, filename)


@app.route('/memes')
def list_memes():
    """Return a list of all generated meme filenames, newest first."""
    os.makedirs(FINAL_IMAGES_DIR, exist_ok=True)
    files = sorted(
        [f for f in os.listdir(FINAL_IMAGES_DIR) if f.lower().endswith(('.jpg', '.jpeg', '.png'))],
        reverse=True
    )
    return jsonify({'memes': files})


if __name__ == '__main__':
    os.makedirs('original_images', exist_ok=True)
    os.makedirs('final_images', exist_ok=True)
    app.run(debug=True)
