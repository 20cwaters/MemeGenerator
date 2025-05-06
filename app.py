from flask import Flask, render_template, jsonify, send_file
import os
from autoposter import get_meme_template, save_image, analyze_image, generate_meme_caption, create_image

app = Flask(__name__)

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/generate-meme', methods=['POST'])
def generate_meme():
    try:
        # Step 1: Get meme template
        image_url = get_meme_template()
        
        if image_url:
            saved_image_path = save_image(image_url, save_directory="original_images")
            if saved_image_path:
                # Step 2: Analyze the image
                image_analysis = analyze_image(saved_image_path)
                if image_analysis:
                    # Step 3: Generate context-aware meme caption
                    text = generate_meme_caption(image_analysis)
                    
                    # Step 4: Create meme with the template and caption
                    final_image_path = create_image(text, saved_image_path)
                    
                    # Return the path to the generated meme
                    return jsonify({
                        'success': True,
                        'image_path': final_image_path
                    })
        
        return jsonify({
            'success': False,
            'error': 'Failed to generate meme'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        })

@app.route('/get-meme/<path:filename>')
def get_meme(filename):
    return send_file(filename, mimetype='image/jpeg')

if __name__ == '__main__':
    # Create necessary directories
    os.makedirs('original_images', exist_ok=True)
    os.makedirs('final_images', exist_ok=True)
    app.run(debug=True) 